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