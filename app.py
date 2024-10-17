from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
from datetime import datetime
import os
import io
import re
import numpy as np
from operations import save_bank_data, get_all_banks, update_bank_data, get_bank_by_id, delete_bank_data, create_table_if_not_exists, save_invoice_data, get_all_invoices
from operations import update_invoice_data, get_invoice_by_id, delete_invoice_data
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
        version = request.form['version']

        # Save the new bank data
        success = save_bank_data(bank_code, bank_name, version)

        if success:
            flash('Bank data added successfully!', 'success')
        else:
            flash('Duplicate entry! Bank data already exists.', 'warning')

    # Fetch all bank data after insert
    banks = get_all_banks()

    # Render the dashboard with the 'add-data-bank' section visible
    return render_template('dashboard.html', banks=banks, show_section='data-bank')


@app.route('/edit_bank/<int:bank_id>', methods=['GET', 'POST'])
def edit_bank(bank_id):
    if request.method == 'POST':
        bank_code = request.form['bank_code']
        bank_name = request.form['bank_name']
        version = request.form['version']

        # Update the bank record
        update_bank_data(bank_id, bank_code, bank_name, version)

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
    create_table_if_not_exists()

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

# Route to generate report
# @app.route('/report/<filenames>')
# def generate_report(filenames):
#     file_list = filenames.split(',')  # Get the list of filenames from the URL
#     reports = []

#     for filename in file_list:
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
#         # Split the filename to extract details
#         name_parts = filename.split('.')
#         bank_code = name_parts[0]
#         channel_type = name_parts[1]
#         year_month = name_parts[2]
#         finance_type = name_parts[3].replace('.csv', '')

#         # Extract year and month details
#         year = year_month[:4]
#         month = int(year_month[4:])
#         month_name = month_names_indonesian[month]

#         # Read the CSV file
#         df = pd.read_csv(filepath)
        
#         # Use regex to remove the fractional seconds from the datetime strings
#         df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))  # Remove everything after the dot (fractional seconds)

#         # Convert the cleaned datetime column to proper datetime format and format as 'mm-dd-yyyy'
#         df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')

#         # Drop rows where datetime conversion failed
#         df = df.dropna(subset=['datetime'])
#         # Pivot the data using the 'count' for non-finance and 'amount' for finance
#         if finance_type == 'finance':
#             pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
#         else:
#             pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='count', aggfunc='sum', fill_value=0)

#         # Add 'Grand Total' column
#         pivot_df['Grand Total'] = pivot_df.sum(axis=1)

#         # Add 'Finance Type' column
#         pivot_df['Finance Type'] = 'Finansial' if finance_type == 'finance' else 'Non-Finansial'

#         # Store each generated report in a list
#         reports.append({
#             'bank_code': bank_code,
#             'channel_type': channel_type,
#             'month_name': month_name,
#             'year': year,
#             'pivot_table': pivot_df
#         })

#     # Render the reports page, passing multiple reports
#     return render_template('pivot_report.html', reports=reports, filenames=filenames)


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



@app.route('/invoice/excel/<filenames>', methods=['GET', 'POST'])
def generate_invoice_to_excel(filenames):
    file_list = filenames.split(',')
    
    # Dictionary to store data grouped by (bank_code, channel_type)
    grouped_files = {}

    # Extract bank code and year/month from the first file for dynamic filename
    first_filename = file_list[0]
    name_parts = first_filename.split('.')
    bank_code = name_parts[0]
    year_month = name_parts[2]

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

    excel_output = io.BytesIO()
    
    # Create an Excel file for the invoice
    with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
        worksheet = writer.book.add_worksheet('Invoice')

        # Initialize row position to write data
        row_position = 0

        # Create combined formats (bold, font size, borders, and background color)
        bold_format = writer.book.add_format({'bold': True})
        bold_font_blue = writer.book.add_format({'bold': True, 'font_size': 14})  # Blue background with border
        border_format_comma = writer.book.add_format({'num_format': '[$-421]#,##0', 'border': 1})
        border_format = writer.book.add_format({'border': 1})  # Border format for regular cells
        bold_border_format_blue = writer.book.add_format({'bold': True, 'border': 1, 'bg_color': '#87CEEB', 'num_format': '[$Rp. -421]#,##0'})  # Bold, blue background
        red_border_format = writer.book.add_format({'bold': True, 'font_color': 'white', 'bg_color': 'red', 'border': 1, 'num_format': '[$Rp. -421]#,##0'})  # Red background with border

        idr_format = writer.book.add_format({
            'num_format': '[$Rp. -421]#,##0',  # IDR format for currency
            'border': 1  # Add border to the cell
        })
                
        grand_total_finance = 0
        grand_total_non_finance = 0

        # Iterate through the groups and generate the invoices
        for (bank_code, channel_type), files in grouped_files.items():
            # Dictionary to store aggregated data for this group
            invoice_data = {}
            allowed_non_finance_keterangans = [
                "Account Statement Inquiry", "CIF Inquiry", 
                "Deposit Accounts Inquiry", "Loan Accounts Inquiry", "Mini Statement"
            ]

            for filepath, finance_type in files:
                # Read the CSV file
                df = pd.read_csv(filepath)
                df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x)) 
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')
                df = df.dropna(subset=['datetime'])

                # Aggregate data for the invoice table
                if finance_type == 'finance':
                    df_agg = df.groupby('keterangan')['amount'].count().reset_index()  # Use count for finance
                    for _, row in df_agg.iterrows():
                        if row['keterangan'] not in invoice_data:
                            invoice_data[row['keterangan']] = {'Non-Finansial': 0, 'Finansial': 0}
                        invoice_data[row['keterangan']]['Finansial'] += row['amount']
                else:
                    df_agg = df.groupby('keterangan')['count'].sum().reset_index()
                    df_agg = df_agg[df_agg['keterangan'].isin(allowed_non_finance_keterangans)]
                    for _, row in df_agg.iterrows():
                        if row['keterangan'] not in invoice_data:
                            invoice_data[row['keterangan']] = {'Non-Finansial': 0, 'Finansial': 0}
                        invoice_data[row['keterangan']]['Non-Finansial'] += row['count']

            # Calculate Grand Total
            grand_total_non_finance += sum([data['Non-Finansial'] for data in invoice_data.values()])
            grand_total_finance += sum([data['Finansial'] for data in invoice_data.values()])

            # Write the bank code and channel type, bold and font size 14 with blue background
            worksheet.write(row_position, 0, f'Bank {bank_code}, {channel_type}', bold_font_blue)
            row_position += 2  # Leave a blank row

            # Write the headers for the table with blue background and borders
            worksheet.write(row_position, 0, 'Keterangan', bold_border_format_blue)
            worksheet.write(row_position, 1, 'Non-Finansial', bold_border_format_blue)
            worksheet.write(row_position, 2, 'Finansial', bold_border_format_blue)

            # Write the invoice data with borders
            row_position += 1
            for keterangan, values in invoice_data.items():
                worksheet.write(row_position, 0, keterangan, border_format)
                worksheet.write(row_position, 1, values['Non-Finansial'], border_format_comma)
                worksheet.write(row_position, 2, values['Finansial'], border_format_comma)
                row_position += 1

            # Write the Grand Total row, bold and with blue background
            worksheet.write(row_position, 0, 'Grand Total', bold_border_format_blue)
            worksheet.write(row_position, 1, sum([data['Non-Finansial'] for data in invoice_data.values()]), border_format_comma)
            worksheet.write(row_position, 2, sum([data['Finansial'] for data in invoice_data.values()]), border_format_comma)

            # Add some space before the next invoice
            row_position += 3  # Leave space for the next group of data

        # After the invoice table, calculate and display the calculation invoice

        col_position = 5  # Place 2 cells to the right of the first invoice
        
        # Write calculation header with borders
        worksheet.write(0, col_position, "Biaya Minimum: Rp. 25,000,000", bold_format)
        row_position = 2
        
        worksheet.write(row_position, col_position, "Transaksi:", bold_format)
        # Extract year and month details from year_month
        year = year_month[:4]
        month = int(year_month[4:])  # Extract the month number

        # Get the month name from the month_names_indonesian list
        month_name = month_names_indonesian[month]

        # Write the month name and year instead of year_month
        worksheet.write(row_position, col_position + 1, f"{month_name} {year}", bold_format)

        worksheet.write(row_position, col_position + 2, "Jumlah Trx", bold_format)
        worksheet.write(row_position, col_position + 3, "Harga", bold_format)
        worksheet.write(row_position, col_position + 4, "Tagihan", bold_format)
        row_position += 1

        # Finansial with borders applied
        worksheet.write(row_position, col_position, "Fin", bold_format)
        worksheet.write(row_position, col_position + 1, grand_total_finance, border_format_comma)
        worksheet.write(row_position, col_position + 2, "", border_format)
        worksheet.write(row_position, col_position + 3, "", border_format)
        worksheet.write(row_position, col_position + 4, "", border_format)
        remaining_finance = grand_total_finance

        # Step by step calculation for different ranges, applying borders
        # Transaksi Finansial 0 - 10000
        calc_1 = min(10000, remaining_finance)
        worksheet.write(row_position + 1, col_position, "", border_format)
        worksheet.write(row_position + 1, col_position + 1, "Transaksi Finansial 0 - 10000", border_format)
        worksheet.write(row_position + 1, col_position + 2, calc_1, border_format_comma)
        worksheet.write(row_position + 1, col_position + 3, 1500, idr_format)
        worksheet.write(row_position + 1, col_position + 4, calc_1 * 1500, idr_format)
        remaining_finance -= calc_1

        # Transaksi Finansial 10,001 - 35,000
        calc_2 = min(25000, remaining_finance)
        worksheet.write(row_position + 2, col_position, "", border_format)
        worksheet.write(row_position + 2, col_position + 1, "Transaksi Finansial 10.001 - 35.000", border_format)
        worksheet.write(row_position + 2, col_position + 2, calc_2, border_format_comma)
        worksheet.write(row_position + 2, col_position + 3, 1200, idr_format)
        worksheet.write(row_position + 2, col_position + 4, calc_2 * 1200, idr_format)
        remaining_finance -= calc_2

        # Transaksi Finansial 35,001 - 75,000
        calc_3 = min(40000, remaining_finance)
        worksheet.write(row_position + 3, col_position, "", border_format)
        worksheet.write(row_position + 3, col_position + 1, "Transaksi Finansial 35.001 - 75.000", border_format)
        worksheet.write(row_position + 3, col_position + 2, calc_3, border_format_comma)
        worksheet.write(row_position + 3, col_position + 3, 1000, idr_format)
        worksheet.write(row_position + 3, col_position + 4, calc_3 * 1000, idr_format)
        remaining_finance -= calc_3

        # Transaksi Finansial 75,001 - 100,000
        calc_4 = min(25000, remaining_finance)
        worksheet.write(row_position + 4, col_position, "", border_format)
        worksheet.write(row_position + 4, col_position + 1, "Transaksi Finansial 75.001 - 100.000", border_format)
        worksheet.write(row_position + 4, col_position + 2, calc_4, border_format_comma)
        worksheet.write(row_position + 4, col_position + 3, 800, idr_format)
        worksheet.write(row_position + 4, col_position + 4, calc_4 * 800, idr_format)
        remaining_finance -= calc_4

        # Transaksi Finansial > 100,000
        calc_5 = remaining_finance
        worksheet.write(row_position + 5, col_position, "", border_format)
        worksheet.write(row_position + 5, col_position + 1, "Transaksi Finansial > 100.000", border_format)
        worksheet.write(row_position + 5, col_position + 2, calc_5, border_format_comma)
        worksheet.write(row_position + 5, col_position + 3, 600, idr_format)
        worksheet.write(row_position + 5, col_position + 4, calc_5 * 600, idr_format)

        # Non-Finansial with borders
        worksheet.write(row_position + 6, col_position, "Non Fin", bold_format)
        worksheet.write(row_position + 6, col_position + 1, grand_total_non_finance, border_format_comma)
        worksheet.write(row_position + 6, col_position + 2, "", border_format)
        worksheet.write(row_position + 6, col_position + 3, "", border_format)
        worksheet.write(row_position + 6, col_position + 4, "", border_format)
        worksheet.write(row_position + 7, col_position, "", border_format)
        worksheet.write(row_position + 7, col_position + 1, "", border_format)
        worksheet.write(row_position + 7, col_position + 2, grand_total_non_finance, border_format_comma)  # Inquiry calculation
        worksheet.write(row_position + 7, col_position + 3, 300, idr_format)
        worksheet.write(row_position + 7, col_position + 4, grand_total_non_finance * 300, idr_format)

        # Total row with borders
        total_tagihan = (
            calc_1 * 1500 + calc_2 * 1200 + calc_3 * 1000 + calc_4 * 800 + calc_5 * 600 +
            grand_total_non_finance * 300
        )
        worksheet.write(row_position + 8, col_position, "", border_format)
        worksheet.write(row_position + 8, col_position + 1, "", border_format)
        worksheet.write(row_position + 8, col_position + 2, "", border_format)
        worksheet.write(row_position + 8, col_position + 3, "", border_format)
        worksheet.write(row_position + 8, col_position + 4, "", border_format)
        worksheet.write(row_position + 9, col_position, "", border_format)
        worksheet.write(row_position + 9, col_position + 1, "", border_format)
        worksheet.write(row_position + 9, col_position + 2, "", border_format)
        worksheet.write(row_position + 9, col_position + 3, "", border_format)
        worksheet.write(row_position + 9, col_position + 4, "", border_format)
        worksheet.write(row_position + 10, col_position, "TOTAL", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 1, "", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 2, "", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 3, "", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 4, "", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 4, total_tagihan, bold_border_format_blue)

        # Total Tagihan with red and border
        total_final = total_tagihan - 25000000
        worksheet.write(row_position + 11, col_position, "Total Tagihan", red_border_format)
        worksheet.write(row_position + 11, col_position + 1, "", red_border_format)
        worksheet.write(row_position + 11, col_position + 2, "", red_border_format)
        worksheet.write(row_position + 11, col_position + 3, "", red_border_format)
        worksheet.write(row_position + 11, col_position + 4, "", red_border_format)
        worksheet.write(row_position + 11, col_position + 4, total_final, red_border_format)


    # Reset the pointer to the beginning of the stream
    excel_output.seek(0)

    # Create the dynamic download filename
    download_name = f"Invoice.{bank_code}.{year_month}.xlsx"

    # Send the file to the user
    return send_file(excel_output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=download_name)


@app.route('/report/<filenames>', methods=['GET', 'POST'])
def generate_report(filenames):
    file_list = filenames.split(',')  # Get the list of filenames from the URL
    reports = []
    all_non_finance_keterangans = set()
    all_finance_keterangans = set()  # Initialize set for financial keterangans

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
        filenames=filenames
    )

# Invoice Combine Route
@app.route('/invoice/combine/<filenames>', methods=['POST'])
def invoice_combine(filenames):
    selected_non_finance_keterangans = request.form.getlist('non_finance_keterangans')
    selected_finance_keterangans = request.form.getlist('finance_keterangans')
    
    if not selected_non_finance_keterangans and not selected_finance_keterangans:
        flash('Please select at least one keterangan to include.', 'warning')
        return redirect(url_for('generate_report', filenames=filenames))
    
    file_list = filenames.split(',')
    excel_output = io.BytesIO()  # Create an in-memory file
    # Extract details from the first file for naming purposes
    first_filename = file_list[0]
    name_parts = first_filename.split('.')
    bank_code = name_parts[0]  # Extract bank code
    year_month = name_parts[2]  # Extract year and month
    # Prepare the month and year for naming
    year = year_month[:4]
    month = int(year_month[4:])
    month_name = month_names_indonesian[month]
    with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
        
        row_position = 0  # To track the row position for writing each report sequentially
        # Create 'Rekap' worksheet
        workbook = writer.book
        worksheet_rekap = workbook.add_worksheet('Rekap')
        # Create formats
        border_format = workbook.add_format({'border': 1})
        bold_format = workbook.add_format({'bold': True})
        header_format = workbook.add_format({'bold': True, 'border': 1})
        keterangan_format = workbook.add_format({'bold': True, 'border': 1})
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
            df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            df = df.dropna(subset=['datetime'])
            df['datetime'] = df['datetime'].dt.strftime('%d-%m-%Y')  # Format as 'dd-mm-yyyy'
            # Sort the DataFrame by datetime
            df = df.sort_values('datetime')
            # Pivot the data based on finance type
            if finance_type == 'finance':
                pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
            else:
                pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='count', aggfunc='sum', fill_value=0)
            # Reorder columns to ensure consistent ordering
            pivot_df = pivot_df.reindex(sorted(pivot_df.columns), axis=1)
            # Add 'Grand Total' and 'Finance Type'
            pivot_df['Grand Total'] = pivot_df.sum(axis=1)
            pivot_df['Finance Type'] = 'Finansial' if finance_type == 'finance' else 'Non-Finansial'
            # Move 'Finance Type' to the first column
            cols = pivot_df.columns.tolist()
            cols = ['Finance Type'] + [col for col in cols if col not in ['Finance Type', 'Grand Total']] + ['Grand Total']
            pivot_df = pivot_df[cols]
            # Write the bank details
            worksheet_rekap.write(row_position, 0, f"Rekap Transaksi Bulanan", bold_format)
            row_position += 1
            worksheet_rekap.write(row_position, 0, f"Bank: {bank_code} | Channel Type: {channel_type} | Bulan: {month_name}, {year}", bold_format)
            row_position += 1
            # Set index name if not set
            if pivot_df.index.name is None:
                pivot_df.index.name = 'keterangan'
            # Prepare the headers
            # Prepare the headers in the new order
            col_labels = ['keterangan', 'Finance Type', 'Grand Total'] + [col for col in pivot_df.columns if col not in ['Finance Type', 'Grand Total']]

            for col_num, value in enumerate(col_labels):
                worksheet_rekap.write(row_position, col_num, value, header_format)
            # Write the data rows
            for df_row_num, (idx, row) in enumerate(pivot_df.reset_index().iterrows()):
                row_values = row.tolist()  # Use row.tolist() directly to include 'keterangan'
                for col_num, cell_value in enumerate(row_values):
                    # Ensure cell_value is of acceptable type
                    if pd.isnull(cell_value):
                        cell_value = ''
                    elif isinstance(cell_value, (np.integer, np.int64, int)):
                        cell_value = int(cell_value)
                    elif isinstance(cell_value, (np.floating, np.float64, float)):
                        cell_value = float(cell_value)
                    else:
                        cell_value = str(cell_value)
                    # Apply bold formatting to 'keterangan' column values
                    if col_num == 0:
                        cell_format = keterangan_format
                    else:
                        cell_format = border_format
                    worksheet_rekap.write(row_position + df_row_num + 1, col_num, cell_value, cell_format)
            # Adjust column widths
            worksheet_rekap.set_column(0, len(col_labels) - 1, 15)
            # Update row_position
            row_position += len(pivot_df) + 2 + 2  # Data rows + headers + extra space
        ### Write the 'Invoice' sheet (from generate_invoice_to_excel)
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
        # Create 'Invoice' worksheet
        worksheet = workbook.add_worksheet('Invoice')
        # Initialize row position to write data
        row_position = 0
        # Create formats
        bold_format = workbook.add_format({'bold': True})
        bold_font_blue = workbook.add_format({'bold': True, 'font_size': 14})
        border_format_comma = workbook.add_format({'num_format': '#,##0', 'border': 1})
        border_format = workbook.add_format({'border': 1})
        bold_border_format = workbook.add_format({'border': 1, 'bold':True})
        bold_border_format_blue = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#87CEEB', 'num_format': '#,##0'})
        red_border_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': 'red', 'border': 1, 'num_format': '#,##0'})
        idr_format = workbook.add_format({'num_format': '"Rp"#,##0', 'border': 1})
        grand_total_finance = 0
        grand_total_non_finance = 0
        # Iterate through the groups and generate the invoices
        for (bank_code, channel_type), files in grouped_files.items():
            # Dictionary to store aggregated data for this group
            invoice_data = {}
            allowed_non_finance_keterangans = selected_non_finance_keterangans
            allowed_finance_keterangans = selected_finance_keterangans
            for filepath, finance_type in files:
                # Read the CSV file
                df = pd.read_csv(filepath)
                df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
                df = df.dropna(subset=['datetime'])
                df['datetime'] = df['datetime'].dt.strftime('%d-%m-%Y')  # Format as 'dd-mm-yyyy'
                # Aggregate data for the invoice table
                if finance_type == 'finance':
                    df_agg = df.groupby('keterangan')['amount'].count().reset_index()
                    df_agg = df_agg[df_agg['keterangan'].isin(allowed_finance_keterangans)]
                    for _, row in df_agg.iterrows():
                        if row['keterangan'] not in invoice_data:
                            invoice_data[row['keterangan']] = {'Non-Finansial': 0, 'Finansial': 0}
                        invoice_data[row['keterangan']]['Finansial'] += row['amount']
                else:
                    df_agg = df.groupby('keterangan')['count'].sum().reset_index()
                    df_agg = df_agg[df_agg['keterangan'].isin(allowed_non_finance_keterangans)]
                    for _, row in df_agg.iterrows():
                        if row['keterangan'] not in invoice_data:
                            invoice_data[row['keterangan']] = {'Non-Finansial': 0, 'Finansial': 0}
                        invoice_data[row['keterangan']]['Non-Finansial'] += row['count']
            # Calculate Grand Total
            grand_total_non_finance += sum([data['Non-Finansial'] for data in invoice_data.values()])
            grand_total_finance += sum([data['Finansial'] for data in invoice_data.values()])
            # Write the bank code and channel type
            worksheet.write(row_position, 0, f'Bank {bank_code}, {channel_type}', bold_font_blue)
            row_position += 2  # Leave a blank row
            # Write the headers for the table
            worksheet.write(row_position, 0, 'Keterangan', bold_border_format_blue)
            worksheet.write(row_position, 1, 'Non-Finansial', bold_border_format_blue)
            worksheet.write(row_position, 2, 'Finansial', bold_border_format_blue)
            # Write the invoice data
            row_position += 1
            for keterangan, values in invoice_data.items():
                worksheet.write(row_position, 0, keterangan, border_format)
                worksheet.write(row_position, 1, values['Non-Finansial'], border_format_comma)
                worksheet.write(row_position, 2, values['Finansial'], border_format_comma)
                row_position += 1
            # Write the Grand Total row
            worksheet.write(row_position, 0, 'Grand Total', bold_border_format_blue)
            worksheet.write(row_position, 1, sum([data['Non-Finansial'] for data in invoice_data.values()]), border_format_comma)
            worksheet.write(row_position, 2, sum([data['Finansial'] for data in invoice_data.values()]), border_format_comma)
            # Add some space before the next invoice
            row_position += 3  # Leave space for the next group of data
        # After the invoice table, calculate and display the calculation invoice
        col_position = 5  # Place 2 cells to the right of the first invoice
        # Write calculation header
        worksheet.write(0, col_position, "Biaya Minimum: Rp. 25,000,000", bold_format)
        row_position = 2
        worksheet.write(row_position, col_position, "Transaksi:", bold_border_format_blue)
        worksheet.write(row_position, col_position + 1, f"{month_name} {year}", bold_border_format_blue)
        worksheet.write(row_position, col_position + 2, "Jumlah Trx", bold_border_format_blue)
        worksheet.write(row_position, col_position + 3, "Harga", bold_border_format_blue)
        worksheet.write(row_position, col_position + 4, "Tagihan", bold_border_format_blue)
        row_position += 1
        # Finansial
        worksheet.write(row_position, col_position, "Fin", bold_border_format)
        worksheet.write(row_position, col_position + 1, grand_total_finance, border_format_comma)
        worksheet.write(row_position, col_position + 2, "", border_format)
        worksheet.write(row_position, col_position + 3, "", border_format)
        worksheet.write(row_position, col_position + 4, "", border_format)
        remaining_finance = grand_total_finance
        # Step by step calculation for different ranges
        # Transaksi Finansial 0 - 10,000
        calc_1 = min(10000, remaining_finance)
        worksheet.write(row_position + 1, col_position, "", border_format)
        worksheet.write(row_position + 1, col_position + 1, "Transaksi Finansial 0 - 10.000", border_format)
        worksheet.write(row_position + 1, col_position + 2, calc_1, border_format_comma)
        worksheet.write(row_position + 1, col_position + 3, 1500, idr_format)
        worksheet.write(row_position + 1, col_position + 4, calc_1 * 1500, idr_format)
        remaining_finance -= calc_1
        # Transaksi Finansial 10,001 - 35,000
        calc_2 = min(25000, remaining_finance)
        worksheet.write(row_position + 2, col_position, "", border_format)
        worksheet.write(row_position + 2, col_position + 1, "Transaksi Finansial 10.001 - 35.000", border_format)
        worksheet.write(row_position + 2, col_position + 2, calc_2, border_format_comma)
        worksheet.write(row_position + 2, col_position + 3, 1200, idr_format)
        worksheet.write(row_position + 2, col_position + 4, calc_2 * 1200, idr_format)
        remaining_finance -= calc_2
        # Transaksi Finansial 35,001 - 75,000
        calc_3 = min(40000, remaining_finance)
        worksheet.write(row_position + 3, col_position, "", border_format)
        worksheet.write(row_position + 3, col_position + 1, "Transaksi Finansial 35.001 - 75.000", border_format)
        worksheet.write(row_position + 3, col_position + 2, calc_3, border_format_comma)
        worksheet.write(row_position + 3, col_position + 3, 1000, idr_format)
        worksheet.write(row_position + 3, col_position + 4, calc_3 * 1000, idr_format)
        remaining_finance -= calc_3
        # Transaksi Finansial 75,001 - 100,000
        calc_4 = min(25000, remaining_finance)
        worksheet.write(row_position + 4, col_position, "", border_format)
        worksheet.write(row_position + 4, col_position + 1, "Transaksi Finansial 75.001 - 100.000", border_format)
        worksheet.write(row_position + 4, col_position + 2, calc_4, border_format_comma)
        worksheet.write(row_position + 4, col_position + 3, 800, idr_format)
        worksheet.write(row_position + 4, col_position + 4, calc_4 * 800, idr_format)
        remaining_finance -= calc_4
        # Transaksi Finansial > 100,000
        calc_5 = remaining_finance
        worksheet.write(row_position + 5, col_position, "", border_format)
        worksheet.write(row_position + 5, col_position + 1, "Transaksi Finansial > 100.000", border_format)
        worksheet.write(row_position + 5, col_position + 2, calc_5, border_format_comma)
        worksheet.write(row_position + 5, col_position + 3, 600, idr_format)
        worksheet.write(row_position + 5, col_position + 4, calc_5 * 600, idr_format)
        # Non-Finansial
        worksheet.write(row_position + 6, col_position, "Non Fin", bold_border_format)
        worksheet.write(row_position, col_position + 1, grand_total_non_finance, border_format_comma)
        worksheet.write(row_position + 6, col_position + 1, "", border_format)
        worksheet.write(row_position + 6, col_position + 2, "", border_format)
        worksheet.write(row_position + 6, col_position + 3, "", border_format)
        worksheet.write(row_position + 6, col_position + 4, "", border_format)
        worksheet.write(row_position + 7, col_position, "", border_format)
        worksheet.write(row_position + 7, col_position + 1, "", border_format)
        worksheet.write(row_position + 7, col_position + 2, grand_total_non_finance, border_format_comma)
        worksheet.write(row_position + 7, col_position + 3, 300, idr_format)
        worksheet.write(row_position + 7, col_position + 4, grand_total_non_finance * 300, idr_format)
        # Total row
        total_tagihan = (
            calc_1 * 1500 + calc_2 * 1200 + calc_3 * 1000 + calc_4 * 800 + calc_5 * 600 +
            grand_total_non_finance * 300
        )
        worksheet.write(row_position + 8, col_position, "", border_format)
        worksheet.write(row_position + 8, col_position + 1, "", border_format)
        worksheet.write(row_position + 8, col_position + 2, "", border_format)
        worksheet.write(row_position + 8, col_position + 3, "", border_format)
        worksheet.write(row_position + 8, col_position + 4, "", border_format)
        worksheet.write(row_position + 9, col_position, "", border_format)
        worksheet.write(row_position + 9, col_position + 1, "", border_format)
        worksheet.write(row_position + 9, col_position + 2, "", border_format)
        worksheet.write(row_position + 9, col_position + 3, "", border_format)
        worksheet.write(row_position + 9, col_position + 4, "", border_format)
        worksheet.write(row_position + 10, col_position, "TOTAL", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 1, "", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 2, "", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 3, "", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 4, "", bold_border_format_blue)
        worksheet.write(row_position + 10, col_position + 4, total_tagihan, bold_border_format_blue)
        # Total Tagihan with red and border
        total_final = total_tagihan - 25000000
        worksheet.write(row_position + 11, col_position, "Total Tagihan", red_border_format)
        worksheet.write(row_position + 11, col_position + 1, "", red_border_format)
        worksheet.write(row_position + 11, col_position + 2, "", red_border_format)
        worksheet.write(row_position + 11, col_position + 3, "", red_border_format)
        worksheet.write(row_position + 11, col_position + 4, "", red_border_format)
        worksheet.write(row_position + 11, col_position + 4, total_final, red_border_format)
    # Reset file pointer to the start of the stream
    excel_output.seek(0)
    # Create the dynamic download filename
    download_name = f"Rekap Kelebihan Transaksi.{bank_code}.{year_month}.xlsx"
    # Send the file to the user
    return send_file(excel_output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=download_name)



if __name__ == '__main__':
    app.run(debug=True)