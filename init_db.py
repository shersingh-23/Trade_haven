import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # # Users table
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS users (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name TEXT NOT NULL,
    #     email TEXT UNIQUE NOT NULL,
    #     password TEXT NOT NULL,
    #     balance REAL DEFAULT 100000,
    #     is_admin INTEGER DEFAULT 0
    # );
    # ''')

     # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        balance REAL DEFAULT 100000,
        is_admin INTEGER DEFAULT 0,
        reset_code TEXT
    );
    ''')

    # Watchlist table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stock_symbol TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')

    # Portfolio table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stock_symbol TEXT,
        quantity INTEGER,
        avg_buy_price REAL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')

    # Transactions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        stock_symbol TEXT,
        quantity INTEGER,
        price REAL,
        type TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')

    # Support table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS support (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        message TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')

    # Admin-added stocks
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE,
        price REAL,
        high REAL,
        low REAL,
        sentiment TEXT
    );
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized.")


if __name__ == '__main__':
    init_db()
