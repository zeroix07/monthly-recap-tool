import sqlite3

def save_bank_data(bank_code, bank_name):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS bank_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            bank_code TEXT NOT NULL,
                            bank_name TEXT NOT NULL,
                            UNIQUE(bank_code, bank_name)
                        )''')

        cursor.execute('''SELECT * FROM bank_data WHERE bank_code = ? AND bank_name = ?''',
                       (bank_code, bank_name))
        result = cursor.fetchone()

        if result:
            return False  # Indicate failure due to duplicate
        else:
            cursor.execute('''INSERT INTO bank_data (bank_code, bank_name)
                              VALUES (?, ?)''', (bank_code, bank_name))
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

def update_bank_data(bank_id, bank_code, bank_name):
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE bank_data
                      SET bank_code = ?, bank_name = ?
                      WHERE id = ?''', (bank_code, bank_name, bank_id))
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
    create_data_biller_table()

def create_bank_data_table():
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS bank_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bank_code TEXT NOT NULL,
                        bank_name TEXT NOT NULL,
                        UNIQUE(bank_code, bank_name)
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

def create_data_biller_table():
    """
    Creates the data_biller table if it does not exist.
    """
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_biller (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_month TEXT NOT NULL,
            bank_code TEXT NOT NULL,
            finance_type TEXT NOT NULL,
            tiering_name TEXT NOT NULL,
            grand_total_finance INTEGER NOT NULL,
            charge INTEGER NOT NULL,
            grand_total_non_finance INTEGER NOT NULL,
            total_tagihan INTEGER NOT NULL,
            total_final INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_data_biller(year_month, bank_code, finance_type, tiering_name, grand_total_finance, charge, grand_total_non_finance, total_tagihan, total_final):
    """
    Inserts a new record into the data_biller table.
    """
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO data_biller (
            year_month,
            bank_code,
            finance_type,
            tiering_name,
            grand_total_finance,
            charge,
            grand_total_non_finance,
            total_tagihan,
            total_final
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        year_month,
        bank_code,
        finance_type,
        tiering_name,
        grand_total_finance,
        charge,
        grand_total_non_finance,
        total_tagihan,
        total_final
    ))
    conn.commit()
    conn.close()


def get_all_data_biller():
    """
    Retrieves all records from the data_biller table.
    """
    conn = sqlite3.connect('database/recap_invoice.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data_biller")
    data_biller = cursor.fetchall()
    conn.close()
    return data_biller if data_biller else []