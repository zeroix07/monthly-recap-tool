import sqlite3

def save_bank_data(bank_code, bank_name, version):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()

    # Create table with UNIQUE constraint
    cursor.execute('''CREATE TABLE IF NOT EXISTS bank_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bank_code TEXT NOT NULL,
                        bank_name TEXT NOT NULL,
                        version TEXT NOT NULL,
                        UNIQUE(bank_code, bank_name, version)
                    )''')

    # Check if the entry already exists
    cursor.execute('''SELECT * FROM bank_data WHERE bank_code = ? AND bank_name = ? AND version = ?''',
                   (bank_code, bank_name, version))
    result = cursor.fetchone()

    if result:
        # Entry already exists, do not insert again
        conn.close()
        return False  # Indicate failure due to duplicate
    else:
        # Insert the new record
        cursor.execute('''INSERT INTO bank_data (bank_code, bank_name, version)
                          VALUES (?, ?, ?)''', (bank_code, bank_name, version))
        conn.commit()
        conn.close()
        return True  # Indicate success


def get_all_banks():
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()

    # Fetch all bank records
    cursor.execute("SELECT * FROM bank_data")
    banks = cursor.fetchall()  # Fetch all rows from the bank_data table

    conn.close()

    # If no records are found, return an empty list
    return banks if banks else []


def get_bank_by_id(bank_id):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM bank_data WHERE id = ?''', (bank_id,))
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
