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
        file = request.files['file']
        if file.filename.endswith('.csv'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            return redirect(url_for('generate_report', filename=file.filename))
        else:
            flash('Please upload a valid CSV file.')
            return redirect(request.url)
    return render_template('upload.html')

month_names_indonesian = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni", 
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

# Route to generate report
@app.route('/report/<filename>')
def generate_report(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Split the filename to extract details
    name_parts = filename.split('.')
    bank_code = name_parts[0]  # Extract bank code (e.g., 'BAG')
    channel_type = name_parts[1]  # Extract channel type (e.g., 'IB' or 'IBB')
    year_month = name_parts[2]  # Extract year and month (e.g., '20245')
    finance_type = name_parts[3].replace('.csv', '')  # Extract finance type (e.g., 'finance' or 'non-finance')

    # Extract year and month details
    year = year_month[:4]  # First 4 digits represent the year (2024)
    month = int(year_month[4:])  # Last digit represents the month (5)
    month_name = month_names_indonesian[month]  # Get the month name in Indonesian

    # Read the CSV file
    df = pd.read_csv(filepath)
    
    # Parse 'datetime' column, handle inconsistent formats with errors='coerce'
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')
    
    # Drop rows where 'datetime' could not be parsed
    df = df.dropna(subset=['datetime'])
    
    # Pivot the data to count occurrences instead of summing the amount
    pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
    
    # Add a 'Grand Total' column (count the total occurrences for each 'keterangan')
    pivot_df['Grand Total'] = pivot_df.sum(axis=1)

    # Add a new 'Finance Type' column after 'Grand Total'
    pivot_df['Finance Type'] = 'Finansial' if finance_type == 'finance' else 'Non-Finansial'
    
    # Pass the DataFrame directly, not as HTML
    return render_template('pivot_report.html', pivot_table=pivot_df,
                           bank_code=bank_code, channel_type=channel_type, month_name=month_name, year=year)



if __name__ == '__main__':
    app.run(debug=True)
