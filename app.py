from flask import Flask, render_template, request, redirect, url_for, flash, send_file, redirect, jsonify
import sqlite3
import pandas as pd
from datetime import datetime
import os
import io
import re
import numpy as np
from operations import (
    save_bank_data, get_all_banks, update_bank_data, get_bank_by_id, delete_bank_data,
    create_table_if_not_exists, get_bank_by_code,
    # New imports for financial invoice
    save_financial_invoice, get_all_financial_invoices,
    update_financial_invoice, get_financial_invoice_by_id, delete_financial_invoice,
    # New imports for non-financial invoice
    save_non_financial_invoice, get_all_non_financial_invoices,
    update_non_financial_invoice, get_non_financial_invoice_by_id, delete_non_financial_invoice,
    get_invoice_data_by_bank_code, save_selected_filters, get_selected_filters,
    save_data_biller
)


from time import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/check_non_financial_tiers')
def check_non_financial_tiers():
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    
    # Check if any non-financial tiers exist
    cursor.execute('SELECT COUNT(*) FROM non_financial_invoice_data')
    count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({'is_first_tier': count == 0})

@app.route('/data_invoice', methods=['GET', 'POST'])
def data_invoice():
    if request.method == 'POST':
        bank_id = request.form.get('bank_id')
        bank = get_bank_by_id(bank_id)
        if not bank:
            flash('Selected bank not found.', 'danger')
            return redirect(url_for('dashboard', show_section='invoice'))

        bank_code = bank[1]
        bank_name = bank[2]
        trx_minimum = request.form.get('trx_minimum')

        if 'save_non_financial' in request.form:
            tiering_name = request.form.get('tiering_name_non_financial')
            nonfinance_price = request.form.get('nonfinance_price')

            # Check if this is the first tier
            conn = sqlite3.connect('database/recap_invoice.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM non_financial_invoice_data')
            is_first_tier = cursor.fetchone()[0] == 0
            conn.close()

            if is_first_tier:
                # For first tier, set trx_nonfinance to 0 as it will be handled dynamically
                trx_nonfinance = 0
            else:
                trx_nonfinance = request.form.get('trx_nonfinance')
                if not trx_nonfinance:
                    flash('Please enter the number of non-financial transactions.', 'warning')
                    return redirect(url_for('data_invoice'))

            success = save_non_financial_invoice(
                bank_code, bank_name, tiering_name, 
                trx_minimum, trx_nonfinance, nonfinance_price
            )

            if success:
                flash('Non-financial invoice saved successfully!', 'success')
            else:
                flash('Duplicate entry! The same non-financial invoice data already exists.', 'warning')

            # After processing, redirect to the invoice section
            return redirect(url_for('dashboard', show_section='invoice'))

        elif 'save_financial' in request.form:
            tiering_name = request.form.get('tiering_name_financial')
            trx_finance = request.form.get('trx_finance')
            finance_price = request.form.get('finance_price')

            # Validate financial transaction inputs
            if not tiering_name or trx_finance is None or finance_price is None:
                flash('Please fill in all Financial transaction fields.', 'warning')
                return redirect(url_for('dashboard', show_section='invoice'))

            success = save_financial_invoice(
                bank_code, bank_name, tiering_name, 
                trx_minimum, trx_finance, finance_price
            )

            if success:
                flash('Financial invoice saved successfully!', 'success')
            else:
                flash('Duplicate entry! The same financial invoice data already exists.', 'warning')

            # After processing, redirect to the invoice section
            return redirect(url_for('dashboard', show_section='invoice'))

    # For GET requests, simply redirect to the dashboard
    return redirect(url_for('dashboard'))


@app.route('/edit_financial_invoice/<int:invoice_id>', methods=['GET', 'POST'])
def edit_financial_invoice(invoice_id):
    if request.method == 'POST':
        bank_id = request.form.get('bank_id')
        bank = get_bank_by_id(bank_id)
        if not bank:
            flash('Selected bank not found.', 'danger')
            return redirect(url_for('data_invoice'))

        bank_code = bank[1]
        bank_name = bank[2]
        tiering_name = request.form.get('tiering_name_financial')
        trx_minimum = request.form.get('trx_minimum')
        trx_finance = request.form.get('trx_finance')
        finance_price = request.form.get('finance_price')

        update_financial_invoice(
            invoice_id, bank_code, bank_name, tiering_name,
            trx_minimum, trx_finance, finance_price
        )
        flash('Financial invoice updated successfully!', 'success')
        return redirect(url_for('data_invoice'))

    # GET request
    invoice = get_financial_invoice_by_id(invoice_id)
    banks = get_all_banks()
    
    # Find the bank ID matching the invoice's bank_code
    invoice_bank_id = None
    for bank in banks:
        if bank[1] == invoice[1]:  # bank[1] is bank_code
            invoice_bank_id = bank[0]
            break

    return render_template('edit_financial_invoice.html',
                         invoice=invoice,
                         banks=banks,
                         invoice_bank_id=invoice_bank_id)

@app.route('/edit_non_financial_invoice/<int:invoice_id>', methods=['GET', 'POST'])
def edit_non_financial_invoice(invoice_id):
    if request.method == 'POST':
        bank_id = request.form.get('bank_id')
        bank = get_bank_by_id(bank_id)
        if not bank:
            flash('Selected bank not found.', 'danger')
            return redirect(url_for('data_invoice'))

        bank_code = bank[1]
        bank_name = bank[2]
        tiering_name = request.form.get('tiering_name_non_financial')
        trx_minimum = request.form.get('trx_minimum')
        trx_nonfinance = request.form.get('trx_nonfinance')
        nonfinance_price = request.form.get('nonfinance_price')

        update_non_financial_invoice(
            invoice_id, bank_code, bank_name, tiering_name,
            trx_minimum, trx_nonfinance, nonfinance_price
        )
        flash('Non-financial invoice updated successfully!', 'success')
        return redirect(url_for('data_invoice'))

    # GET request
    invoice = get_non_financial_invoice_by_id(invoice_id)
    banks = get_all_banks()
    
    # Find the bank ID matching the invoice's bank_code
    invoice_bank_id = None
    for bank in banks:
        if bank[1] == invoice[1]:  # bank[1] is bank_code
            invoice_bank_id = bank[0]
            break

    return render_template('edit_non_financial_invoice.html',
                         invoice=invoice,
                         banks=banks,
                         invoice_bank_id=invoice_bank_id)

@app.route('/delete_financial_invoice/<int:invoice_id>', methods=['POST'])
def handle_delete_financial_invoice(invoice_id):  # Changed function name
    delete_financial_invoice(invoice_id)  # This calls the function from operations.py
    flash('Financial invoice deleted successfully!', 'success')
    return redirect(url_for('data_invoice', show_section='invoice'))

@app.route('/delete_non_financial_invoice/<int:invoice_id>', methods=['POST'])
def handle_delete_non_financial_invoice(invoice_id):  # Changed function name
    delete_non_financial_invoice(invoice_id)  # This calls the function from operations.py
    flash('Non-financial invoice deleted successfully!', 'success')
    return redirect(url_for('data_invoice', show_section='invoice'))


@app.route('/get_bank_code/<int:bank_id>', methods=['GET'])
def get_bank_code(bank_id):
    bank = get_bank_by_id(bank_id)
    if bank:
        return {"bank_code": bank[1]}  # bank_code is at index 1
    else:
        return {"error": "Bank not found"}, 404




@app.route('/data__bank_invoice', methods=['GET', 'POST'])
def data__bank_invoice(): 
    # Fetch the bank data from the bank_data table (replace this with your actual query)
    banks = get_all_banks()  # Example function to fetch bank_code and bank_name from the database

    if request.method == 'POST':
        # Process the form data here (bank_code, bank_name, etc.)
        bank_name = request.form['bank_name']
        # Add your form handling logic here

    return render_template('dashboard.html', banks=banks, show_section='invoice')


@app.route('/add_bank', methods=['POST', 'GET'])
def add_bank():
    if request.method == 'POST':
        bank_code = request.form['bank_code']
        bank_name = request.form['bank_name']

        # Save the new bank data
        success = save_bank_data(bank_code, bank_name)

        if success:
            flash('Bank data added successfully!', 'success')
        else:
            flash('Duplicate entry! Bank data already exists.', 'warning')

    # Fetch all bank data after insert
    banks = get_all_banks()
    financial_invoices = get_all_financial_invoices()
    non_financial_invoices = get_all_non_financial_invoices()
    # Render the dashboard with the 'add-data-bank' section visible
    return render_template('dashboard.html', banks=banks, financial_invoices=financial_invoices, non_financial_invoices=non_financial_invoices, show_section='data-bank')


@app.route('/edit_bank/<int:bank_id>', methods=['GET', 'POST'])
def edit_bank(bank_id):
    if request.method == 'POST':
        bank_code = request.form['bank_code']
        bank_name = request.form['bank_name']

        # Update the bank record
        update_bank_data(bank_id, bank_code, bank_name)

        flash('Bank data updated successfully!', 'success')
        return redirect(url_for('add_bank'))

    # If GET, fetch the bank record
    bank = get_bank_by_id(bank_id)
    return render_template('edit_bank.html', bank=bank)


@app.route('/delete_bank/<int:bank_id>', methods=['GET'])
def delete_bank(bank_id):
    # Delete the bank data
    delete_bank_data(bank_id)

    flash('Bank data deleted successfully!', 'success')

    # Fetch all bank data after deletion
    banks = get_all_banks()

    # Render the dashboard with the 'add-data-bank' section visible
    return render_template('dashboard.html', banks=banks, show_section='data-bank')



@app.route('/', methods=['GET'])
def dashboard():
    banks = get_all_banks()
    financial_invoices = get_all_financial_invoices()
    non_financial_invoices = get_all_non_financial_invoices()

    show_section = request.args.get('show_section', 'welcome')

    return render_template('dashboard.html',
                         banks=banks,
                         financial_invoices=financial_invoices,
                         non_financial_invoices=non_financial_invoices,
                         show_section=show_section)


# Change the route from '/' to '/upload'
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('files')  # Get the list of uploaded files
        file_paths = []

        # Loop through the files and save them
        for file in files:
            if file.filename.endswith('.csv'):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                file_paths.append(file.filename)  # Store filenames for report generation
            else:
                flash('Please upload valid CSV files.')
                return redirect(request.url)

        # Redirect to the report generation page with the list of filenames
        return redirect(url_for('generate_report', filenames=",".join(file_paths)))

    # Since the form is in dashboard.html, you might not need to render 'upload.html' here
    # But if you still want to render 'upload.html' on GET request to '/upload', you can keep this
    return render_template('dashboard.html')


month_names_indonesian = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]


# Export route to generate Excel file in the same format as pivot report
@app.route('/export/<filenames>')
def export_to_excel(filenames):
    file_list = filenames.split(',')
    excel_output = io.BytesIO()  # Create an in-memory file

    # Extract details from the first file for naming purposes
    first_filename = file_list[0]
    name_parts = first_filename.split('.')
    bank_code = name_parts[0]  # Extract bank code
    year_month = name_parts[2]  # Extract year and month
    finance_type = name_parts[3].replace('.csv', '')  # Extract finance type

    # Extract year and month details from the first file
    year = year_month[:4]
    month = int(year_month[4:])
    month_name = month_names_indonesian[month]  # Get the month name in Indonesian

    with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
        row_position = 0  # To track the row position for writing each report sequentially

        for filename in file_list:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Split the filename to extract details
            name_parts = filename.split('.')
            bank_code = name_parts[0]
            channel_type = name_parts[1]
            year_month = name_parts[2]
            finance_type = name_parts[3].replace('.csv', '')

            # Extract year and month details
            year = year_month[:4]
            month = int(year_month[4:])
            month_name = month_names_indonesian[month]

            # Read the CSV file
            df = pd.read_csv(filepath)
            df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))  # Remove everything after the dot (fractional seconds)

            # Convert the cleaned datetime column to proper datetime format and format as 'mm-dd-yyyy'
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')

            # Drop rows where datetime conversion failed
            df = df.dropna(subset=['datetime'])

            # Pivot the data based on finance type
            if finance_type == 'finance':
                pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
            else:
                pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='count', aggfunc='sum', fill_value=0)

            # Add 'Grand Total' and 'Finance Type'
            pivot_df['Grand Total'] = pivot_df.sum(axis=1)
            pivot_df['Finance Type'] = 'Finansial' if finance_type == 'finance' else 'Non-Finansial'

            # Write the bank details
            worksheet = writer.sheets.get('Rekap') or writer.book.add_worksheet('Rekap')
            worksheet.write(row_position, 0, f"Rekap Transaksi Bulanan")
            row_position += 1
            worksheet.write(row_position, 0, f"Bank: {bank_code} | Channel Type: {channel_type} | Bulan: {month_name}, {year}")
            row_position += 1

            # Write the pivot table data to the Excel sheet
            pivot_df.to_excel(writer, sheet_name='Rekap', startrow=row_position, header=True, index=True)

            # Adjust column widths for better readability
            worksheet.set_column(0, len(pivot_df.columns), 15)  # Adjust column widths as needed

            # Apply a border format to all cells
            workbook = writer.book
            border_format = workbook.add_format({
                'border': 1  # Adds a solid border to all sides of the cell
            })

            # Get the DataFrame as a 2D list of values
            data_with_headers = [pivot_df.columns.insert(0, 'Keterangan')] + pivot_df.reset_index().values.tolist()

            # Apply the border format to all cells
            for row_num, row_data in enumerate(data_with_headers, start=row_position):
                for col_num, cell_value in enumerate(row_data):
                    worksheet.write(row_num + 1, col_num, cell_value, border_format)

            # Move the row position down to leave space before the next report
            row_position += len(pivot_df) + 4

    # Reset file pointer to the start of the stream
    excel_output.seek(0)

    # Generate the download name using the first file's details
    download_name = f"Transaksi_Bulanan_{bank_code}_{month_name}_{year}.xlsx"

    # Send the Excel file to the user
    return send_file(excel_output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=download_name)

@app.route('/report/<filenames>', methods=['GET', 'POST'])
def generate_report(filenames):
    file_list = filenames.split(',')  # Get the list of filenames from the URL
    reports = []
    all_non_finance_keterangans = set()
    all_finance_keterangans = set()  # Initialize set for financial keterangans

    # Extract bank code from the first filename
    first_filename = file_list[0]
    bank_code = first_filename.split('.')[0]

    # Get bank name
    bank = get_bank_by_code(bank_code)
    bank_name = bank[2] if bank else 'Unknown'

    # Get previously selected filters
    finance_selected, non_finance_selected = get_selected_filters(bank_code)

    for filename in file_list:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            flash(f'File {filename} does not exist.', 'danger')
            continue  # Skip missing files

        # Split the filename to extract details
        name_parts = filename.split('.')
        if len(name_parts) < 4:
            flash(f'Filename {filename} does not conform to expected format.', 'warning')
            continue  # Skip improperly formatted filenames

        bank_code = name_parts[0]
        channel_type = name_parts[1]
        year_month = name_parts[2]
        finance_type = name_parts[3].replace('.csv', '')

        # Extract year and month details
        year = year_month[:4]
        try:
            month = int(year_month[4:])
            month_name = month_names_indonesian[month]
        except (ValueError, IndexError):
            flash(f'Invalid year_month format in filename {filename}.', 'warning')
            continue  # Skip files with invalid month

        # Read the CSV file
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            flash(f'Error reading {filename}: {e}', 'danger')
            continue  # Skip files that cannot be read

        # Use regex to remove the fractional seconds from the datetime strings
        df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))  # Remove fractional seconds

        # Convert the cleaned datetime column to proper datetime format and format as 'mm-dd-yyyy'
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')

        # Drop rows where datetime conversion failed
        df = df.dropna(subset=['datetime'])

        # Collect unique keterangans based on finance type
        if finance_type != 'finance':
            non_finance_keterangans = df['keterangan'].dropna().unique()
            all_non_finance_keterangans.update(non_finance_keterangans)
        else:
            finance_keterangans = df['keterangan'].dropna().unique()
            all_finance_keterangans.update(finance_keterangans)

        # Pivot the data using the appropriate columns
        if finance_type == 'finance':
            if 'amount' not in df.columns:
                flash(f"'amount' column missing in {filename} for finance type.", 'warning')
                continue  # Skip if 'amount' column is missing
            pivot_df = df.pivot_table(
                index='keterangan', 
                columns='datetime', 
                values='amount', 
                aggfunc='count', 
                fill_value=0
            )
        else:
            if 'count' not in df.columns:
                flash(f"'count' column missing in {filename} for non-finance type.", 'warning')
                continue  # Skip if 'count' column is missing
            pivot_df = df.pivot_table(
                index='keterangan', 
                columns='datetime', 
                values='count', 
                aggfunc='sum', 
                fill_value=0
            )

        # Add 'Grand Total' column
        pivot_df['Grand Total'] = pivot_df.sum(axis=1)

        # Add 'Finance Type' column
        pivot_df['Finance Type'] = 'Finansial' if finance_type == 'finance' else 'Non-Finansial'

        # Store each generated report in a list
        reports.append({
            'bank_code': bank_code,
            'channel_type': channel_type,
            'month_name': month_name,
            'year': year,
            'pivot_table': pivot_df
        })

    # Convert the sets to sorted lists
    unique_non_finance_keterangans = sorted(all_non_finance_keterangans)
    unique_finance_keterangans = sorted(all_finance_keterangans)

    if not reports:
        flash('No valid reports generated. Please check your files.', 'danger')

    # Render the reports page, passing multiple reports and the unique keterangans
    return render_template(
        'pivot_report.html', 
        reports=reports,
        unique_non_finance_keterangans=unique_non_finance_keterangans,
        unique_finance_keterangans=unique_finance_keterangans,
        filenames=filenames,
        finance_selected=finance_selected,
        non_finance_selected=non_finance_selected
    )

@app.route('/invoice/combine/<filenames>', methods=['POST'])
def invoice_combine(filenames):
    selected_non_finance_keterangans = request.form.getlist('non_finance_keterangans')
    selected_finance_keterangans = request.form.getlist('finance_keterangans')

    # Extract bank_code from filenames
    file_list = filenames.split(',')
    first_filename = file_list[0]
    bank_code = first_filename.split('.')[0].strip()

    # Get bank_name from bank_data table
    bank = get_bank_by_code(bank_code)
    if bank:
        bank_name = bank[2]  # bank_name is at index 2
    else:
        flash(
            f'Bank code "{bank_code}" not found in the database. Please add the bank data before proceeding.',
            'danger'
        )
        return redirect(url_for('generate_report', filenames=filenames))

    # Save the selected filters to the database
    save_selected_filters(
        bank_code, bank_name, selected_finance_keterangans, selected_non_finance_keterangans
    )

    if not selected_non_finance_keterangans and not selected_finance_keterangans:
        flash('Please select at least one keterangan to include.', 'warning')
        return redirect(url_for('generate_report', filenames=filenames))

    # Fetch invoice data for both financial and non-financial
    financial_data = []
    non_financial_data = []
    
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    
    # Get financial invoice data
    cursor.execute('''
        SELECT tiering_name_financial, trx_minimum, trx_finance, finance_price 
        FROM financial_invoice_data 
        WHERE bank_code = ?
    ''', (bank_code,))
    financial_rows = cursor.fetchall()
    for row in financial_rows:
        financial_data.append({
            'tiering_name': row[0],
            'trx_minimum': row[1],
            'trx_finance': row[2],
            'finance_price': row[3]
        })

    # Get non-financial invoice data
    cursor.execute('''
        SELECT tiering_name_non_financial, trx_minimum, trx_nonfinance, nonfinance_price 
        FROM non_financial_invoice_data 
        WHERE bank_code = ?
    ''', (bank_code,))
    non_financial_rows = cursor.fetchall()
    for row in non_financial_rows:
        non_financial_data.append({
            'tiering_name': row[0],
            'trx_minimum': row[1],
            'trx_nonfinance': row[2],
            'nonfinance_price': row[3]
        })
    
    conn.close()

    if not financial_data and not non_financial_data:
        flash(
            f'No invoice data found for bank code "{bank_code}". Please add the invoice data before proceeding.',
            'danger'
        )
        return redirect(url_for('generate_report', filenames=filenames))

    # Create Excel file
    excel_output = io.BytesIO()
    
    # Get month and year from filename
    year_month_raw = first_filename.split('.')[2]
    year = year_month_raw[:4]
    month = int(year_month_raw[4:])
    month_name = month_names_indonesian[month]
    year_month = f"{month:02d}-{year}"

    with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Define formats
        border_format = workbook.add_format({'border': 1})
        bold_border_format = workbook.add_format({'border': 1, 'bold': True})
        border_format_comma = workbook.add_format({'num_format': '#,##0', 'border': 1})
        idr_format = workbook.add_format({'num_format': '"Rp"#,##0', 'border': 1})
        bold_border_format_blue = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#87CEEB', 'num_format': '#,##0'
        })
        red_border_format = workbook.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': 'red', 'border': 1,
            'num_format': '#,##0'
        })
        bold_font_blue = workbook.add_format({'bold': True, 'font_size': 14})
        # Create 'Rekap' sheet
        worksheet_rekap = workbook.add_worksheet('Rekap')
        row_position = 0

        for filename in file_list:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            name_parts = filename.split('.')
            bank_code = name_parts[0]
            channel_type = name_parts[1]
            year_month_file = name_parts[2]
            finance_type = name_parts[3].replace('.csv', '')
            
            # Read and process CSV file
            df = pd.read_csv(filepath)
            df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            df = df.dropna(subset=['datetime'])
            df['datetime'] = df['datetime'].dt.strftime('%d-%m-%Y')
            df = df.sort_values('datetime')

            # Filter data and create pivot table
            if finance_type == 'finance':
                df = df[df['keterangan'].isin(selected_finance_keterangans)]
                pivot_df = df.pivot_table(
                    index='keterangan',
                    columns='datetime',
                    values='amount',
                    aggfunc='count',
                    fill_value=0
                )
                finance_type_label = 'Finansial'
            else:
                df = df[df['keterangan'].isin(selected_non_finance_keterangans)]
                pivot_df = df.pivot_table(
                    index='keterangan',
                    columns='datetime',
                    values='count',
                    aggfunc='sum',
                    fill_value=0
                )
                finance_type_label = 'Non-Finansial'

            # Sort date columns
            date_columns = sorted(
                [col for col in pivot_df.columns if isinstance(col, str)],
                key=lambda x: datetime.strptime(x, '%d-%m-%Y')
            )
            pivot_df = pivot_df[date_columns]
            
            # Add totals
            pivot_df['Grand Total'] = pivot_df.sum(axis=1)
            pivot_df['Finance Type'] = finance_type_label

            # Write to Rekap sheet
            worksheet_rekap.write(row_position, 0, "Rekap Transaksi Bulanan", bold_font_blue)
            row_position += 1
            worksheet_rekap.write(
                row_position, 0,
                f"Bank: {bank_code} | Channel Type: {channel_type} | Bulan: {month_name}, {year}",
                bold_font_blue
            )
            row_position += 1

            # Write headers
            headers = ['keterangan', 'Finance Type', 'Grand Total'] + date_columns
            for col_num, header in enumerate(headers):
                worksheet_rekap.write(row_position, col_num, header, bold_border_format_blue)

            # Write data
            pivot_df.reset_index(inplace=True)
            for row_idx, row in pivot_df.iterrows():
                for col_idx, value in enumerate(row):
                    if isinstance(value, (int, float)):
                        worksheet_rekap.write(row_position + 1 + row_idx, col_idx, value, border_format_comma)
                    else:
                        worksheet_rekap.write(row_position + 1 + row_idx, col_idx, value, border_format)

            # Write grand total row
            worksheet_rekap.write(row_position + len(pivot_df) + 1, 0, 'Grand Total', bold_border_format_blue)
            worksheet_rekap.write(row_position + len(pivot_df) + 1, 1, '', bold_border_format_blue)
            
            for col_idx, col in enumerate(date_columns, start=2):
                col_total = pivot_df[col].sum()
                worksheet_rekap.write(row_position + len(pivot_df) + 1, col_idx, col_total, bold_border_format_blue)

            final_total = pivot_df['Grand Total'].sum()
            worksheet_rekap.write(
                row_position + len(pivot_df) + 1, 
                len(headers) - 1, 
                final_total, 
                bold_border_format_blue
            )

            row_position += len(pivot_df) + 3

        # Adjust Rekap column widths
        worksheet_rekap.set_column(0, len(headers) - 1, 15)

        # Create 'Invoice' sheet
        worksheet = workbook.add_worksheet('Invoice')

        # Group data by channel type from filenames
        channel_groups = {}
        for filename in file_list:
            name_parts = filename.split('.')
            channel_type = name_parts[1]
            if channel_type not in channel_groups:
                channel_groups[channel_type] = {
                    'files': [],
                    'financial_data': {},
                    'non_financial_data': {}
                }
            channel_groups[channel_type]['files'].append(filename)

        # Process data for each channel type
        current_row = 0
        grand_total_finance_all = 0
        grand_total_non_finance_all = 0

        for channel_type, group_data in channel_groups.items():
            # Write channel group header
            worksheet.write(current_row, 0, f"{bank_name}, {channel_type}", bold_font_blue)
            current_row += 1

            # Write table headers
            worksheet.write(current_row, 0, "Keterangan", bold_border_format_blue)
            worksheet.write(current_row, 1, "Non-Finansial", bold_border_format_blue)
            worksheet.write(current_row, 2, "Finansial", bold_border_format_blue)
            current_row += 1

            # Initialize dictionaries to store values for each keterangan
            financial_totals = {k: 0 for k in selected_finance_keterangans}
            non_financial_totals = {k: 0 for k in selected_non_finance_keterangans}
            
            # Process files for this channel type
            for filename in group_data['files']:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                finance_type = filename.split('.')[3].replace('.csv', '')
                
                df = pd.read_csv(filepath)
                if finance_type == 'finance':
                    df = df[df['keterangan'].isin(selected_finance_keterangans)]
                    for keterangan in selected_finance_keterangans:
                        count = len(df[df['keterangan'] == keterangan])
                        financial_totals[keterangan] += count
                else:
                    df = df[df['keterangan'].isin(selected_non_finance_keterangans)]
                    for keterangan in selected_non_finance_keterangans:
                        count = df[df['keterangan'] == keterangan]['count'].sum()
                        non_financial_totals[keterangan] += count

            # Combine all unique keterangans
            all_keterangans = sorted(set(list(financial_totals.keys()) + list(non_financial_totals.keys())))

            # Write data rows
            grand_total_fin = 0
            grand_total_non_fin = 0
            for keterangan in all_keterangans:
                worksheet.write(current_row, 0, keterangan, border_format)
                
                # Write non-financial value
                non_fin_value = non_financial_totals.get(keterangan, 0)
                worksheet.write(current_row, 1, non_fin_value, border_format_comma)
                grand_total_non_fin += non_fin_value
                
                # Write financial value
                fin_value = financial_totals.get(keterangan, 0)
                worksheet.write(current_row, 2, fin_value, border_format_comma)
                grand_total_fin += fin_value
                
                current_row += 1

            # Write grand total row for this channel type
            worksheet.write(current_row, 0, "Grand Total", bold_border_format_blue)
            worksheet.write(current_row, 1, grand_total_non_fin, bold_border_format_blue)
            worksheet.write(current_row, 2, grand_total_fin, bold_border_format_blue)
            current_row += 2  # Add extra space between channel groups

            # Add to overall totals
            grand_total_finance_all += grand_total_fin
            grand_total_non_finance_all += grand_total_non_fin

        # Get minimum fee
        if financial_data:
            trx_minimum = financial_data[0]['trx_minimum']
        elif non_financial_data:
            trx_minimum = non_financial_data[0]['trx_minimum']
        else:
            trx_minimum = 0

        # Start position for calculation table
        col_position = 5

        # Write minimum fee and continue with calculations
        worksheet.write(0, col_position, f"Biaya Minimum: Rp. {trx_minimum:,}", bold_font_blue)
        
        calculation_row = 2
        worksheet.write(calculation_row, col_position, "Transaksi:", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 1, f"{month_name} {year}", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 2, "Jumlah Trx", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 3, "Harga", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 4, "Tagihan", bold_border_format_blue)
        calculation_row += 1

        # Initialize total tagihan
        total_tagihan = 0

        # Process Financial Transactions
        if financial_data:
            worksheet.write(calculation_row, col_position, "Fin", bold_border_format)
            worksheet.write(calculation_row, col_position + 1, grand_total_finance_all, border_format_comma)
            worksheet.write(calculation_row, col_position + 2, "", border_format)
            worksheet.write(calculation_row, col_position + 3, "", border_format)
            worksheet.write(calculation_row, col_position + 4, "", border_format)
            calculation_row += 1

            for tier in financial_data:
                charge = tier['trx_finance'] * tier['finance_price']
                total_tagihan += charge

                worksheet.write(calculation_row, col_position, "", border_format)
                worksheet.write(calculation_row, col_position + 1, tier['tiering_name'], border_format)
                worksheet.write(calculation_row, col_position + 2, tier['trx_finance'], border_format_comma)
                worksheet.write(calculation_row, col_position + 3, tier['finance_price'], idr_format)
                worksheet.write(calculation_row, col_position + 4, charge, idr_format)
                calculation_row += 1

                save_data_biller(
                    year_month=year_month,
                    bank_code=bank_code,
                    finance_type='Finansial',
                    tiering_name=tier['tiering_name'],
                    grand_total_finance=grand_total_finance_all,
                    charge=charge,
                    grand_total_non_finance=grand_total_non_finance_all,
                    total_tagihan=total_tagihan,
                    total_final=0
                )

        # Process Non-Financial Transactions
        if non_financial_data:
            worksheet.write(calculation_row, col_position, "Non Fin", bold_border_format)
            worksheet.write(calculation_row, col_position + 1, grand_total_non_finance_all, border_format_comma)
            worksheet.write(calculation_row, col_position + 2, "", border_format)
            worksheet.write(calculation_row, col_position + 3, "", border_format)
            worksheet.write(calculation_row, col_position + 4, "", border_format)
            calculation_row += 1

            # Process each non-financial tier
            for index, tier in enumerate(non_financial_data):
                # For the first tier, use grand_total_non_finance_all instead of trx_nonfinance
                if index == 0:
                    trx_value = grand_total_non_finance_all
                else:
                    trx_value = tier['trx_nonfinance']
                
                charge = trx_value * tier['nonfinance_price']
                total_tagihan += charge

                worksheet.write(calculation_row, col_position, "", border_format)
                worksheet.write(calculation_row, col_position + 1, tier['tiering_name'], border_format)
                worksheet.write(calculation_row, col_position + 2, trx_value, border_format_comma)
                worksheet.write(calculation_row, col_position + 3, tier['nonfinance_price'], idr_format)
                worksheet.write(calculation_row, col_position + 4, charge, idr_format)
                calculation_row += 1

                save_data_biller(
                    year_month=year_month,
                    bank_code=bank_code,
                    finance_type='Non-Finansial',
                    tiering_name=tier['tiering_name'],
                    grand_total_finance=grand_total_finance_all,
                    charge=charge,
                    grand_total_non_finance=grand_total_non_finance_all,
                    total_tagihan=total_tagihan,
                    total_final=0
                )
                
        # Write total charges
        worksheet.write(calculation_row, col_position, "TOTAL", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 1, "", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 2, "", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 3, "", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 4, total_tagihan, bold_border_format_blue)
        calculation_row += 1

        # Apply minimum charge calculation
        total_final = total_tagihan - trx_minimum

        # Write final total
        worksheet.write(calculation_row, col_position, "Total Tagihan", red_border_format)
        worksheet.write(calculation_row, col_position + 1, "", red_border_format)
        worksheet.write(calculation_row, col_position + 2, "", red_border_format)
        worksheet.write(calculation_row, col_position + 3, "", red_border_format)
        worksheet.write(calculation_row, col_position + 4, total_final, red_border_format)

        # Update total_final in data_biller
        conn = sqlite3.connect('database/recap_invoice.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE data_biller
            SET total_final = ?
            WHERE year_month = ? AND bank_code = ?
        ''', (total_final, year_month, bank_code))
        conn.commit()
        conn.close()

    # Reset file pointer
    excel_output.seek(0)
    
    # Create download filename
    download_name = f"Rekap Kelebihan Transaksi.{bank_code}.{year_month_raw}.xlsx"
    
    return send_file(
        excel_output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=download_name
    )


if __name__ == '__main__':
    create_table_if_not_exists()
    app.run(debug=True)