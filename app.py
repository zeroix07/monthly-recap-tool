from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import os
from datetime import datetime
import io

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
        
        # Parse 'datetime' column
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')
        df = df.dropna(subset=['datetime'])

        # Pivot the data using the 'count' for non-finance and 'amount' for finance
        if finance_type == 'finance':
            pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
        else:
            pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='count', aggfunc='count', fill_value=0)

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


# Export route to generate Excel file
from flask import send_file
import io
import pandas as pd

# Export route to generate Excel file in the same format as pivot report
@app.route('/export/<filenames>')
def export_to_excel(filenames):
    file_list = filenames.split(',')
    excel_output = io.BytesIO()  # Create an in-memory file

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
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')
            df = df.dropna(subset=['datetime'])

            # Pivot the data based on finance type
            if finance_type == 'finance':
                pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
            else:
                pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='count', aggfunc='count', fill_value=0)

            # Add 'Grand Total' and 'Finance Type'
            pivot_df['Grand Total'] = pivot_df.sum(axis=1)
            pivot_df['Finance Type'] = 'Finansial' if finance_type == 'finance' else 'Non-Finansial'

            # Write the bank details
            worksheet = writer.sheets.get('Report') or writer.book.add_worksheet('Report')
            worksheet.write(row_position, 0, f"Rekap Transaksi Bulanan")
            row_position += 1
            worksheet.write(row_position, 0, f"Bank: {bank_code} | Channel Type: {channel_type} | Bulan: {month_name}, {year}")
            row_position += 1

            # Write the pivot table data
            pivot_df.to_excel(writer, sheet_name='Report', startrow=row_position, header=True, index=True)

            # Adjust column widths for better readability
            for col_num, value in enumerate(pivot_df.columns):
                worksheet.set_column(col_num + 1, col_num + 1, 15)  # Adjust column widths as needed

            # Move the row position down to leave space before the next report
            row_position += len(pivot_df) + 4

    # Reset file pointer to the start of the stream
    excel_output.seek(0)

    # Send the Excel file to the user
    return send_file(excel_output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name='transaction_report.xlsx')





if __name__ == '__main__':
    app.run(debug=True)
