import sqlite3

def save_bank_data(bank_code, bank_name, version):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS bank_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            bank_code TEXT NOT NULL,
                            bank_name TEXT NOT NULL,
                            version TEXT NOT NULL,
                            UNIQUE(bank_code, bank_name, version)
                        )''')

        cursor.execute('''SELECT * FROM bank_data WHERE bank_code = ? AND bank_name = ? AND version = ?''',
                       (bank_code, bank_name, version))
        result = cursor.fetchone()

        if result:
            return False  # Indicate failure due to duplicate
        else:
            cursor.execute('''INSERT INTO bank_data (bank_code, bank_name, version)
                              VALUES (?, ?, ?)''', (bank_code, bank_name, version))
            conn.commit()
            return True  # Indicate success
    finally:
        conn.close()


def get_all_banks():
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM bank_data")
        banks = cursor.fetchall()
        return banks if banks else []
    finally:
        conn.close()

def get_bank_by_id(bank_id):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM bank_data WHERE id = ?''', (bank_id,))
    bank = cursor.fetchone()
    conn.close()
    return bank

def get_bank_by_code(bank_code):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bank_data WHERE bank_code = ?', (bank_code,))
    bank = cursor.fetchone()
    conn.close()
    return bank

def update_bank_data(bank_id, bank_code, bank_name, version):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE bank_data
                      SET bank_code = ?, bank_name = ?, version = ?
                      WHERE id = ?''', (bank_code, bank_name, version, bank_id))
    conn.commit()
    conn.close()

def delete_bank_data(bank_id):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM bank_data WHERE id = ?''', (bank_id,))
    conn.commit()
    conn.close()

def get_bank_code_by_id(bank_id):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()

    # Query the bank code using the bank ID
    cursor.execute("SELECT bank_code FROM bank_data WHERE id = ?", (bank_id,))
    bank_code = cursor.fetchone()
    conn.close()

    return bank_code

def create_table_if_not_exists():
    create_bank_data_table()
    create_invoice_data_table()
    create_selected_filters_table()

def create_bank_data_table():
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS bank_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bank_code TEXT NOT NULL,
                        bank_name TEXT NOT NULL,
                        version TEXT NOT NULL,
                        UNIQUE(bank_code, bank_name, version)
                    )''')
    conn.commit()
    conn.close()

def create_invoice_data_table():
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS invoice_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bank_code TEXT NOT NULL,
                        bank_name TEXT NOT NULL,
                        tiering_name TEXT NOT NULL,
                        trx_minimum INTEGER NOT NULL,
                        trx_finance INTEGER NOT NULL,
                        finance_price INTEGER NOT NULL,
                        trx_nonfinance INTEGER NOT NULL,
                        nonfinance_price INTEGER NOT NULL,
                        UNIQUE(bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price)
                    )''')
    conn.commit()
    conn.close()

def create_selected_filters_table():
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS selected_filters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_code TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            finance_keterangans TEXT,
            non_finance_keterangans TEXT,
            UNIQUE(bank_code)
        )
    ''')
    conn.commit()
    conn.close()

def save_invoice_data(bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS invoice_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bank_code TEXT NOT NULL,
                        bank_name TEXT NOT NULL,
                        tiering_name TEXT NOT NULL,
                        trx_minimum INTEGER NOT NULL,
                        trx_finance INTEGER NOT NULL,
                        finance_price INTEGER NOT NULL,
                        trx_nonfinance INTEGER NOT NULL,
                        nonfinance_price INTEGER NOT NULL,
                        UNIQUE(bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price)
                    )''')

    cursor.execute('''SELECT * FROM invoice_data WHERE bank_code = ? AND bank_name = ? AND tiering_name = ? 
                      AND trx_minimum = ? AND trx_finance = ? AND finance_price = ? AND trx_nonfinance = ? AND nonfinance_price = ?''',
                   (bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price))
    result = cursor.fetchone()

    if result:
        conn.close()
        return False
    else:
        cursor.execute('''INSERT INTO invoice_data (bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                       (bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price))
        conn.commit()
        conn.close()
        return True

def update_invoice_data(invoice_id, bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    
    cursor.execute('''UPDATE invoice_data
                      SET bank_code = ?, bank_name = ?, tiering_name = ?, trx_minimum = ?, trx_finance = ?, finance_price = ?, trx_nonfinance = ?, nonfinance_price = ?
                      WHERE id = ?''',
                   (bank_code, bank_name, tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price, invoice_id))
    conn.commit()
    conn.close()

def delete_invoice_data(invoice_id):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    
    # Delete the invoice record by its ID
    cursor.execute('''DELETE FROM invoice_data WHERE id = ?''', (invoice_id,))
    
    conn.commit()
    conn.close()

def get_all_invoices():
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()

    # Fetch all invoice records
    cursor.execute("SELECT * FROM invoice_data")
    invoices = cursor.fetchall()

    conn.close()
    return invoices

def get_invoice_by_id(invoice_id):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    
    cursor.execute('''SELECT * FROM invoice_data WHERE id = ?''', (invoice_id,))
    invoice = cursor.fetchone()
    
    conn.close()
    return invoice

def get_invoice_data_by_bank_code(bank_code):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tiering_name, trx_minimum, trx_finance, finance_price, trx_nonfinance, nonfinance_price
        FROM invoice_data
        WHERE bank_code = ?
        ORDER BY id ASC
    ''', (bank_code,))
    data = cursor.fetchall()
    conn.close()
    return data  # Returns a list of tuples


def save_selected_filters(bank_code, bank_name, finance_keterangans, non_finance_keterangans):
    if bank_name is None:
        raise ValueError("bank_name cannot be None")

    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    finance_keterangans_str = ','.join(finance_keterangans)
    non_finance_keterangans_str = ','.join(non_finance_keterangans)

    # Check if the entry already exists
    cursor.execute('SELECT * FROM selected_filters WHERE bank_code = ?', (bank_code,))
    result = cursor.fetchone()

    if result:
        # Update existing entry
        cursor.execute('''
            UPDATE selected_filters
            SET finance_keterangans = ?, non_finance_keterangans = ?
            WHERE bank_code = ?
        ''', (finance_keterangans_str, non_finance_keterangans_str, bank_code))
    else:
        # Insert new entry
        cursor.execute('''
            INSERT INTO selected_filters (bank_code, bank_name, finance_keterangans, non_finance_keterangans)
            VALUES (?, ?, ?, ?)
        ''', (bank_code, bank_name, finance_keterangans_str, non_finance_keterangans_str))
    conn.commit()
    conn.close()

def get_selected_filters(bank_code):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('SELECT finance_keterangans, non_finance_keterangans FROM selected_filters WHERE bank_code = ?', (bank_code,))
    result = cursor.fetchone()
    conn.close()

    if result:
        finance_keterangans = result[0].split(',') if result[0] else []
        non_finance_keterangans = result[1].split(',') if result[1] else []
        # Remove any empty strings from the lists
        finance_keterangans = [k for k in finance_keterangans if k]
        non_finance_keterangans = [k for k in non_finance_keterangans if k]
        return finance_keterangans, non_finance_keterangans
    else:
        return [], []

