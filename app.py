from flask import Flask, render_template, request, redirect, url_for, flash, send_file, redirect
import sqlite3
import pandas as pd
from datetime import datetime
import os
import io
import re
import numpy as np
from operations import (
    save_bank_data, get_all_banks, update_bank_data, get_bank_by_id, delete_bank_data,
    create_table_if_not_exists, save_invoice_data, get_all_invoices,
    update_invoice_data, get_invoice_by_id, delete_invoice_data,
    get_invoice_data_by_bank_code, save_selected_filters, get_selected_filters,
    get_bank_by_code, save_data_biller  # Add this
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


@app.route('/data_invoice', methods=['GET', 'POST'])
def data_invoice():
    banks = get_all_banks()  # Fetch bank data
    invoices = get_all_invoices()  # Always fetch invoice data

    if request.method == 'POST':
        # Handle form submission
        bank_id = request.form.get('bank_id')
        bank = get_bank_by_id(bank_id)
        if bank:
            bank_code = bank[1]  # bank_code
            bank_name = bank[2]  # bank_name
        else:
            flash('Selected bank not found.', 'danger')
            return redirect(url_for('dashboard', show_section='invoice'))

        # Form data
        tiering_name = request.form['tiering_name']
        trx_minimum = request.form['trx_minimum']
        trx_finance = request.form['trx_finance']
        finance_price = request.form['finance_price']
        trx_nonfinance = request.form['trx_nonfinance']
        nonfinance_price = request.form['nonfinance_price']

        # Save invoice data
        success = save_invoice_data(bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price)
        if success:
            flash('Invoice data saved successfully!', 'success')
        else:
            flash('Duplicate entry! The same invoice data already exists.', 'warning')

    # Render the template with all invoice data passed
    return render_template('dashboard.html', banks=banks, invoices=invoices, show_section='invoice')



@app.route('/edit_invoice/<int:invoice_id>', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    if request.method == 'POST':
        bank_id = request.form.get('bank_id')
        bank = get_bank_by_id(bank_id)
        if bank:
            bank_code = bank[1]  # bank_code
            bank_name = bank[2]  # bank_name
        else:
            flash('Selected bank not found.', 'danger')
            return redirect(url_for('data_invoice'))

        tiering_name = request.form['tiering_name']
        trx_minimum = request.form['trx_minimum']
        trx_finance = request.form['trx_finance']
        finance_price = request.form['finance_price']
        trx_nonfinance = request.form['trx_nonfinance']
        nonfinance_price = request.form['nonfinance_price']

        # Update the invoice data
        update_invoice_data(invoice_id, bank_code, bank_name, tiering_name, trx_minimum, trx_finance,
                            finance_price, trx_nonfinance, nonfinance_price)
        flash('Invoice updated successfully!', 'success')

        return redirect(url_for('data_invoice'))

    # Fetch the existing invoice data to pre-fill the form
    invoice = get_invoice_by_id(invoice_id)
    banks = get_all_banks()

    # Find the bank ID corresponding to the invoice's bank_code
    invoice_bank_id = None
    for bank in banks:
        if bank[1] == invoice[1]:  # bank[1] is bank_code
            invoice_bank_id = bank[0]  # bank[0] is bank_id
            break

    return render_template('edit_invoice.html', invoice=invoice, banks=banks, invoice_bank_id=invoice_bank_id)



@app.route('/delete_invoice/<int:invoice_id>', methods=['POST'])
def delete_invoice(invoice_id):
    delete_invoice_data(invoice_id)
    flash('Invoice deleted successfully!', 'success')
    return redirect(url_for('data_invoice'))



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
    invoices = get_all_invoices()
    # Render the dashboard with the 'add-data-bank' section visible
    return render_template('dashboard.html', banks=banks, invoices=invoices, show_section='data-bank')


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
    invoices = get_all_invoices()

    # If no banks exist, pass an empty list
    if not banks:
        banks = []

    show_section = request.args.get('show_section', 'welcome')

    # Render the template with the banks data
    return render_template('dashboard.html', banks=banks, invoices=invoices, show_section=show_section)


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

# app.py

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
        bank_name = bank[2]  # Assuming bank_name is at index 2
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

    # Fetch invoice data for the bank_code
    invoice_data_list = get_invoice_data_by_bank_code(bank_code)
    if not invoice_data_list:
        flash(
            f'No invoice data found for bank code "{bank_code}". Please add the invoice data before proceeding.',
            'danger'
        )
        return redirect(url_for('generate_report', filenames=filenames))

    # Process the invoice data into a list of dictionaries
    invoice_data = []
    for row in invoice_data_list:
        tiering_name = row[0]
        trx_minimum = int(row[1])
        trx_finance = int(row[2])
        finance_price = int(row[3])
        trx_nonfinance = int(row[4])
        nonfinance_price = int(row[5])
        invoice_data.append({
            'tiering_name': tiering_name,
            'trx_minimum': trx_minimum,
            'trx_finance': trx_finance,
            'finance_price': finance_price,
            'trx_nonfinance': trx_nonfinance,
            'nonfinance_price': nonfinance_price
        })

    # Proceed to generate the invoice based on selected filters
    excel_output = io.BytesIO()
    # Prepare the month and year for naming
    name_parts = first_filename.split('.')
    year_month_raw = name_parts[2]
    year = year_month_raw[:4]
    month = int(year_month_raw[4:])
    month_name = month_names_indonesian[month]

    # Format year_month as mm-yyyy
    year_month = f"{month:02d}-{year}"

    with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
        # Initialize workbook and formats
        workbook = writer.book
        border_format = workbook.add_format({'border': 1})
        bold_format = workbook.add_format({'bold': True})
        bold_border_format = workbook.add_format({'bold': True, 'border': 1})
        bold_font_blue = workbook.add_format({'bold': True, 'font_size': 14})
        border_format_comma = workbook.add_format({'num_format': '#,##0', 'border': 1})
        idr_format = workbook.add_format({'num_format': '"Rp"#,##0', 'border': 1})
        bold_border_format_blue = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#87CEEB', 'num_format': '#,##0'
        })
        red_border_format = workbook.add_format({
            'bold': True, 'font_color': 'white', 'bg_color': 'red', 'border': 1,
            'num_format': '#,##0'
        })

        # Generate the 'Rekap' sheet with all data (no filters)
        worksheet_rekap = workbook.add_worksheet('Rekap')
        row_position = 0  # To track the row position for writing each report sequentially

        for filename in file_list:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Split the filename to extract details
            name_parts = filename.split('.')
            bank_code = name_parts[0]
            channel_type = name_parts[1]
            year_month_file = name_parts[2]
            finance_type = name_parts[3].replace('.csv', '')
            # Extract year and month details
            year = year_month_file[:4]
            month = int(year_month_file[4:])
            month_name = month_names_indonesian[month]
            # Read the CSV file
            df = pd.read_csv(filepath)
            df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            df = df.dropna(subset=['datetime'])
            df['datetime'] = df['datetime'].dt.strftime('%d-%m-%Y')  # Format as 'dd-mm-yyyy'
            # Sort the DataFrame by datetime
            df = df.sort_values('datetime')

            # Pivot the data based on finance type (no filters applied)
            if finance_type == 'finance':
                pivot_df = df.pivot_table(
                    index='keterangan', columns='datetime', values='amount',
                    aggfunc='count', fill_value=0
                )
                finance_type_label = 'Finansial'
            else:
                pivot_df = df.pivot_table(
                    index='keterangan', columns='datetime', values='count',
                    aggfunc='sum', fill_value=0
                )
                finance_type_label = 'Non-Finansial'

            # Reorder date columns to ensure consistent ordering
            date_columns = sorted(
                [col for col in pivot_df.columns if isinstance(col, str)],
                key=lambda x: datetime.strptime(x, '%d-%m-%Y')
            )
            pivot_df = pivot_df[date_columns]

            # Add 'Grand Total' and 'Finance Type'
            pivot_df['Grand Total'] = pivot_df.sum(axis=1)
            pivot_df['Finance Type'] = finance_type_label

            # Rearrange columns as per your requirement
            cols = ['keterangan', 'Finance Type', 'Grand Total'] + date_columns
            pivot_df.reset_index(inplace=True)
            pivot_df = pivot_df[cols]

            # Write the bank details
            worksheet_rekap.write(row_position, 0, f"Rekap Transaksi Bulanan", bold_format)
            row_position += 1
            worksheet_rekap.write(
                row_position, 0,
                f"Bank: {bank_code} | Channel Type: {channel_type} | Bulan: {month_name}, {year}",
                bold_format
            )
            row_position += 1

            # Write headers
            for col_num, value in enumerate(cols):
                worksheet_rekap.write(row_position, col_num, value, bold_border_format)
            # Write data rows
            for df_row_num, row in pivot_df.iterrows():
                for col_num, cell_value in enumerate(row):
                    # Ensure cell_value is of acceptable type
                    if pd.isnull(cell_value):
                        cell_value = ''
                    elif isinstance(cell_value, (int, np.integer)):
                        cell_value = int(cell_value)
                    elif isinstance(cell_value, (float, np.floating)):
                        cell_value = float(cell_value)
                    else:
                        cell_value = str(cell_value)
                    worksheet_rekap.write(
                        row_position + df_row_num + 1, col_num, cell_value, border_format_comma
                    )
            # Adjust column widths
            worksheet_rekap.set_column(0, len(cols) - 1, 15)
            # Update row_position
            row_position += len(pivot_df) + 2  # Data rows + headers + extra space

        # Generate 'Invoice' sheet with filtered data
        worksheet = workbook.add_worksheet('Invoice')
        row_position = 0

        # Initialize total variables
        grand_total_finance = 0
        grand_total_non_finance = 0

        # Dictionary to store data grouped by (bank_code, channel_type)
        grouped_files = {}
        # Group the files by bank code and channel type
        for filename in file_list:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # Split the filename to extract details
            name_parts = filename.split('.')
            bank_code = name_parts[0]
            channel_type = name_parts[1]
            finance_type = name_parts[3].replace('.csv', '')
            key = (bank_code, channel_type)  # Grouping key
            if key not in grouped_files:
                grouped_files[key] = []
            grouped_files[key].append((filepath, finance_type))

        for (bank_code, channel_type), files in grouped_files.items():
            # Dictionary to store aggregated data for this group
            invoice_data_values = {}
            for filepath, finance_type in files:
                # Read the CSV file
                df = pd.read_csv(filepath)
                df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
                df = df.dropna(subset=['datetime'])
                df['datetime'] = df['datetime'].dt.strftime('%d-%m-%Y')  # Format as 'dd-mm-yyyy'
                # Filter the data based on selected keterangans
                if finance_type == 'finance':
                    df = df[df['keterangan'].isin(selected_finance_keterangans)]
                else:
                    df = df[df['keterangan'].isin(selected_non_finance_keterangans)]
                # Aggregate data for the invoice table
                if finance_type == 'finance':
                    df_agg = df.groupby('keterangan')['amount'].count().reset_index()
                    for _, row in df_agg.iterrows():
                        if row['keterangan'] not in invoice_data_values:
                            invoice_data_values[row['keterangan']] = {'Non-Finansial': 0, 'Finansial': 0}
                        invoice_data_values[row['keterangan']]['Finansial'] += row['amount']
                else:
                    df_agg = df.groupby('keterangan')['count'].sum().reset_index()
                    for _, row in df_agg.iterrows():
                        if row['keterangan'] not in invoice_data_values:
                            invoice_data_values[row['keterangan']] = {'Non-Finansial': 0, 'Finansial': 0}
                        invoice_data_values[row['keterangan']]['Non-Finansial'] += row['count']
            # Calculate Grand Total
            grand_total_non_finance += sum([data['Non-Finansial'] for data in invoice_data_values.values()])
            grand_total_finance += sum([data['Finansial'] for data in invoice_data_values.values()])
            # Write the bank code and channel type
            worksheet.write(row_position, 0, f'Bank {bank_code}, {channel_type}', bold_font_blue)
            row_position += 2  # Leave a blank row
            # Write the headers for the table
            worksheet.write(row_position, 0, 'Keterangan', bold_border_format_blue)
            worksheet.write(row_position, 1, 'Non-Finansial', bold_border_format_blue)
            worksheet.write(row_position, 2, 'Finansial', bold_border_format_blue)
            # Write the invoice data
            row_position += 1
            for keterangan, values in invoice_data_values.items():
                worksheet.write(row_position, 0, keterangan, border_format)
                worksheet.write(row_position, 1, values['Non-Finansial'], border_format_comma)
                worksheet.write(row_position, 2, values['Finansial'], border_format_comma)
                row_position += 1
            # Write the Grand Total row
            worksheet.write(row_position, 0, 'Grand Total', bold_border_format_blue)
            worksheet.write(row_position, 1, sum([data['Non-Finansial'] for data in invoice_data_values.values()]),
                            border_format_comma)
            worksheet.write(row_position, 2, sum([data['Finansial'] for data in invoice_data_values.values()]),
                            border_format_comma)
            # Add some space before the next invoice
            row_position += 3  # Leave space for the next group of data

        # After the invoice table, calculate and display the calculation invoice
        col_position = 5  # Place cells to the right of the first invoice
        # Write calculation header
        trx_minimum = int(invoice_data[0]['trx_minimum'])  # Assuming trx_minimum is the same across tiers
        worksheet.write(0, col_position, f"Biaya Minimum: Rp. {trx_minimum:,}", bold_format)
        calculation_row = 2

        worksheet.write(calculation_row, col_position, "Transaksi:", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 1, f"{month_name} {year}", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 2, "Jumlah Trx", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 3, "Harga", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 4, "Tagihan", bold_border_format_blue)
        calculation_row += 1

        # Finansial
        worksheet.write(calculation_row, col_position, "Fin", bold_border_format)
        worksheet.write(calculation_row, col_position + 1, grand_total_finance, border_format_comma)
        worksheet.write(calculation_row, col_position + 2, "", border_format)
        worksheet.write(calculation_row, col_position + 3, "", border_format)
        worksheet.write(calculation_row, col_position + 4, "", border_format)
        calculation_row += 1

        # Process each tier directly without calculating remaining_finance
        total_tagihan = 0
        for tier in invoice_data:
            tiering_name = tier['tiering_name']
            trx_finance = tier['trx_finance']
            finance_price = tier['finance_price']

            # Calculate charge based on trx_finance directly
            charge = trx_finance * finance_price

            # Write tier data
            worksheet.write(calculation_row, col_position, "", border_format)
            worksheet.write(calculation_row, col_position + 1, tiering_name, border_format)
            worksheet.write(calculation_row, col_position + 2, trx_finance, border_format_comma)
            worksheet.write(calculation_row, col_position + 3, finance_price, idr_format)
            worksheet.write(calculation_row, col_position + 4, charge, idr_format)

            # Update total charges
            total_tagihan += charge
            calculation_row += 1

            # Insert into data_biller
            save_data_biller(
                year_month=year_month,
                bank_code=bank_code,
                finance_type='Finansial',
                tiering_name=tiering_name,
                grand_total_finance=grand_total_finance,
                charge=charge,
                grand_total_non_finance=grand_total_non_finance,
                total_tagihan=total_tagihan,
                total_final=0  # To be updated after all calculations
            )

        # Handle excess transactions if any (optional)
        # If grand_total_finance > sum of trx_finance, handle accordingly
        sum_trx_finance = sum([tier['trx_finance'] for tier in invoice_data])
        excess_finance = grand_total_finance - sum_trx_finance
        if excess_finance > 0:
            last_price = int(invoice_data[-1]['finance_price'])  # Use last tier price
            charge = excess_finance * last_price

            worksheet.write(calculation_row, col_position, "", border_format)
            worksheet.write(calculation_row, col_position + 1, "Excess Transactions", border_format)
            worksheet.write(calculation_row, col_position + 2, excess_finance, border_format_comma)
            worksheet.write(calculation_row, col_position + 3, last_price, idr_format)
            worksheet.write(calculation_row, col_position + 4, charge, idr_format)

            # Update total charges
            total_tagihan += charge
            calculation_row += 1

            # Insert into data_biller
            save_data_biller(
                year_month=year_month,
                bank_code=bank_code,
                finance_type='Finansial',
                tiering_name='Excess Transactions',
                grand_total_finance=grand_total_finance,
                charge=charge,
                grand_total_non_finance=grand_total_non_finance,
                total_tagihan=total_tagihan,
                total_final=0  # To be updated after all calculations
            )

        # Non-Finansial
        nonfinance_price = int(invoice_data[0]['nonfinance_price'])  # Assuming same price across tiers

        worksheet.write(calculation_row, col_position, "Non Fin", bold_border_format)
        worksheet.write(calculation_row, col_position + 1, grand_total_non_finance, border_format_comma)
        worksheet.write(calculation_row, col_position + 2, "", border_format)
        worksheet.write(calculation_row, col_position + 3, "", border_format)
        worksheet.write(calculation_row, col_position + 4, "", border_format)
        calculation_row += 1

        worksheet.write(calculation_row, col_position, "", border_format)
        worksheet.write(calculation_row, col_position + 1, "Inquiry", border_format)
        worksheet.write(calculation_row, col_position + 2, grand_total_non_finance, border_format_comma)
        worksheet.write(calculation_row, col_position + 3, nonfinance_price, idr_format)
        worksheet.write(calculation_row, col_position + 4, grand_total_non_finance * nonfinance_price, idr_format)

        # Update total charges
        total_tagihan += grand_total_non_finance * nonfinance_price
        calculation_row += 1

        # Insert into data_biller for Non-Finansial
        save_data_biller(
            year_month=year_month,
            bank_code=bank_code,
            finance_type='Non-Finansial',
            tiering_name='Non-Finansial',
            grand_total_finance=grand_total_finance,
            charge=grand_total_non_finance * nonfinance_price,
            grand_total_non_finance=grand_total_non_finance,
            total_tagihan=total_tagihan,
            total_final=0  # To be updated after all calculations
        )

        # Total Charges
        worksheet.write(calculation_row, col_position, "TOTAL", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 1, "", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 2, "", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 3, "", bold_border_format_blue)
        worksheet.write(calculation_row, col_position + 4, total_tagihan, bold_border_format_blue)
        calculation_row += 1

        # Apply Minimum Charge
        trx_minimum = int(invoice_data[0]['trx_minimum'])

        total_final = total_tagihan - trx_minimum
        # Write final total
        worksheet.write(calculation_row, col_position, "Total Tagihan", red_border_format)
        worksheet.write(calculation_row, col_position + 1, "", red_border_format)
        worksheet.write(calculation_row, col_position + 2, "", red_border_format)
        worksheet.write(calculation_row, col_position + 3, "", red_border_format)
        worksheet.write(calculation_row, col_position + 4, total_final, red_border_format)

        # Update data_biller with total_final
        # Fetch all relevant records for this bank_code and year_month
        conn = sqlite3.connect('database/recap_invoice.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE data_biller
            SET total_final = ?
            WHERE year_month = ? AND bank_code = ?
        ''', (total_final, year_month, bank_code))
        conn.commit()
        conn.close()

    # Reset file pointer to the start of the stream
    excel_output.seek(0)
    # Create the dynamic download filename
    download_name = f"Rekap Kelebihan Transaksi.{bank_code}.{year_month_raw}.xlsx"
    # Send the file to the user
    return send_file(
        excel_output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=download_name
    )




if __name__ == '__main__':
    get_all_invoices()
    create_table_if_not_exists()
    app.run(debug=True)