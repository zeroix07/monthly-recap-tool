from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
from datetime import datetime
import os
import io
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Ensure upload directory exists
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to display form and upload CSV
@app.route('/', methods=['GET', 'POST'])
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

    return render_template('upload.html')

month_names_indonesian = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

# Route to generate report
@app.route('/report/<filenames>')
def generate_report(filenames):
    file_list = filenames.split(',')  # Get the list of filenames from the URL
    reports = []

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
        
        # Use regex to remove the fractional seconds from the datetime strings
        df['datetime'] = df['datetime'].apply(lambda x: re.sub(r'\.\d+', '', x))  # Remove everything after the dot (fractional seconds)

        # Convert the cleaned datetime column to proper datetime format and format as 'mm-dd-yyyy'
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')

        # Drop rows where datetime conversion failed
        df = df.dropna(subset=['datetime'])
        # Pivot the data using the 'count' for non-finance and 'amount' for finance
        if finance_type == 'finance':
            pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
        else:
            pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='count', aggfunc='sum', fill_value=0)

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

    # Render the reports page, passing multiple reports
    return render_template('pivot_report.html', reports=reports, filenames=filenames)


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



@app.route('/invoice/excel/<filenames>')
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
        worksheet.write(0, col_position, "Minimum Transaksi: Rp. 25,000,000", bold_format)
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


if __name__ == '__main__':
    app.run(debug=True)
