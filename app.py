from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from datetime import datetime


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

        # Pivot the data
        pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
        pivot_df['Grand Total'] = pivot_df.sum(axis=1)
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
    return render_template('pivot_report.html', reports=reports)




if __name__ == '__main__':
    app.run(debug=True)
