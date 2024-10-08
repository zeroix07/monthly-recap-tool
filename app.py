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

# Route to generate report
@app.route('/report/<filename>')
def generate_report(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_csv(filepath)
    
    # Parse 'datetime' column, handle inconsistent formats with errors='coerce'
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.strftime('%m-%d-%Y')
    
    # Drop rows where 'datetime' could not be parsed
    df = df.dropna(subset=['datetime'])
    
    # Pivot the data to count occurrences instead of summing the amount
    pivot_df = df.pivot_table(index='keterangan', columns='datetime', values='amount', aggfunc='count', fill_value=0)
    
    # Sort 'keterangan' in a case-insensitive way (Aa-Zz)
    pivot_df = pivot_df.reindex(sorted(pivot_df.index, key=lambda x: x.lower()))
    
    # Add a 'Grand Total' column (count the total occurrences for each 'keterangan')
    pivot_df['Grand Total'] = pivot_df.sum(axis=1)
    
    # Render the pivoted report as an HTML table
    return render_template('pivot_report.html', pivot_table=pivot_df.to_html(classes='table table-bordered', border=0))




if __name__ == '__main__':
    app.run(debug=True)
