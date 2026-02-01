from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import math
from datetime import datetime
from init_db import init_db
import io
import csv
import smtplib
from email.mime.text import MIMEText


EMAIL_ADDRESS = "your_gmail@gmail.com"
EMAIL_PASSWORD = "lzyqgfxamzkjdpqs"

SMTP_HOST = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 587


app = Flask(__name__)
app.secret_key = 'supersecretkey'

stocks = {
    'TCS': 3500,
    'INFY': 1500,
    'HDFC': 2700,
    'RELIANCE': 2500,
    'SBIN': 550,
    'WIPRO': 400,
    'ITC': 270,
    'HCLTECH': 1100,
    'LT': 2400,
    'BAJAJFINSV': 15000,
    'HDFCBANK': 1600,
    'AXISBANK': 950,
    'ICICIBANK': 900,
    'KOTAKBANK': 1700,
    'BHARTIARTL': 800,
    'ADANIENT': 2200,
    'COALINDIA': 220,
    'TATAMOTORS': 600,
    'MARUTI': 10000,
    'DRREDDY': 5000,
    'SUNPHARMA': 900,
    'ULTRACEMCO': 8000,
    'NESTLEIND': 22000,
    'ASIANPAINT': 3100,
    'BAJAJ-AUTO': 4300,
    'EICHERMOT': 3700,
    'POWERGRID': 260,
    'TITAN': 3400,
    'DIVISLAB': 3600,
    'NTPC': 250,
    'UPL': 630,
    'TECHM': 1200,
    'HINDUNILVR': 2600,
    'GRASIM': 1800,
    'ONGC': 180,
    'JSWSTEEL': 800,
    'BPCL': 420,
    'INDUSINDBK': 1100,
    'BRITANNIA': 4700,
    'CIPLA': 1300
}


def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def is_admin():
    db = get_db()
    user = db.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return user and user['is_admin'] == 1


def simulate_stock_history(start_price, symbol, years=5, steps_per_year=52):
    steps = years * steps_per_year
    prices = []

    # Consistent hash from symbol string
    hash_val = sum(ord(c) for c in symbol)
    group = hash_val % 10

    # Assign trends: ~60% positive, ~20% flat, ~20% negative
    if group < 6:
        annual_rate = 0.12  # growing
    elif group < 8:
        annual_rate = 0.1  # flat
    else:
        annual_rate = -0.5  # declining

    weekly_rate = (1 + annual_rate) ** (1 / steps_per_year) - 1

    # Volatility using sine wave
    freq = 0.75 + (hash_val % 5) * 0.03  # 0.15 - 0.27
    amp = start_price * 0.22  # 2% volatility

    for t in range(steps):
        trend_price = start_price * ((1 + weekly_rate) ** t)
        wave = math.sin(t * freq) * amp
        price = trend_price + wave
        prices.append(round(price, 2))

    return prices



def get_prediction_from_history(prices):
    n = len(prices)
    x = list(range(n))
    y = prices

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(i * i for i in x)
    sum_xy = sum(x[i] * y[i] for i in range(n))

    denominator = n * sum_xx - sum_x ** 2
    b = (n * sum_xy - sum_x * sum_y) / denominator if denominator != 0 else 0
    a = (sum_y - b * sum_x) / n

    predicted_price = a + b * (n + 1)
    live_price = y[-1]
    profit = ((predicted_price - live_price) / live_price) * 100

    return round(live_price, 2), round(predicted_price, 2), round(profit, 2)

@app.route('/api/chart_data')
def chart_data():
    period = request.args.get('period', 'week')

    length = {
        'week': 7,
        'month': 30,
        'year': 365
    }.get(period, 7)

    base_price = 51800
    data = []
    for _ in range(length):
        base_price += random.uniform(-200, 200)
        data.append(round(base_price, 2))

    return jsonify(data)




@app.route('/')
def home():
    db = get_db()

    # Simulated Sensex value
    sensex_price = round(sum(stocks.values()) / len(stocks) * random.uniform(20, 21))

    # Fake user-friendly transaction table (replace with real JOIN later if needed)
    transactions = [
        {
            'id': 5001, 'date': '2025-05-21', 'from_name': 'Ramesh', 'to_name': 'Suresh',
            'market': 'NSE', 'amount': 5000, 'status': 'Completed'
        },
        {
            'id': 5002, 'date': '2025-05-21', 'from_name': 'Anjali', 'to_name': 'Mehta',
            'market': 'BSE', 'amount': 2500, 'status': 'Pending'
        },
        {
            'id': 5003, 'date': '2025-05-21', 'from_name': 'Divya', 'to_name': 'Arjun',
            'market': 'NSE', 'amount': 8000, 'status': 'Cancelled'
        },
        {
            'id': 5004, 'date': '2025-05-21', 'from_name': 'Sneha', 'to_name': 'Vikram',
            'market': 'BSE', 'amount': 12000, 'status': 'Completed'
        }
    ]

    chart_labels = [f"{i}:00" for i in range(10, 20)]
    chart_data = [round(sensex_price * (0.98 + i * 0.005), 2) for i in range(10)]

    return render_template('home.html', sensex_price=sensex_price,
                           transactions=transactions,
                           chart_labels=chart_labels,
                           chart_data=chart_data)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower().strip()
        password = generate_password_hash(request.form['password'])
        db = get_db()
        try:
            db.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
            db.commit()
            return redirect('/login')
        except:
            error = 'Email already exists.'  # Pass error message instead of plain return
    return render_template('signup.html', error=error)



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password']

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect('/admin' if user['is_admin'] else '/dashboard')
        else:
            error = 'Email and password are incorrect.'  # ✅ This is already here

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/admin')
def admin():
    if 'user_id' not in session or not is_admin():
        return redirect('/login')

    db = get_db()
    users = db.execute('SELECT id, name, email, balance FROM users').fetchall()
    tickets = db.execute('SELECT * FROM support ORDER BY date DESC').fetchall()
    stocks = db.execute('SELECT * FROM stock_list').fetchall()
    return render_template('admin.html', users=users, tickets=tickets, stocks=stocks)


@app.route('/admin/add_stock', methods=['POST'])
def add_stock():
    if 'user_id' not in session or not is_admin():
        return redirect('/login')

    symbol = request.form['symbol'].upper()
    price = float(request.form['price'])
    high = float(request.form['high'])
    low = float(request.form['low'])
    sentiment = request.form['sentiment']

    db = get_db()
    db.execute('''
        INSERT OR REPLACE INTO stock_list (symbol, price, high, low, sentiment)
        VALUES (?, ?, ?, ?, ?)
    ''', (symbol, price, high, low, sentiment))
    db.commit()

    return redirect('/admin')


@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'user_id' not in session or not is_admin():
        return redirect('/login')

    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.execute('DELETE FROM watchlist WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM portfolio WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM support WHERE user_id = ?', (user_id,))
    db.commit()
    return redirect('/admin')

@app.route('/admin/reset_balance/<int:user_id>')
def reset_balance(user_id):
    if 'user_id' not in session or not is_admin():
        return redirect('/login')

    db = get_db()
    db.execute('UPDATE users SET balance = 100000 WHERE id = ?', (user_id,))
    db.commit()
    return redirect('/admin')


@app.route('/admin/delete_ticket/<int:ticket_id>')
def delete_ticket(ticket_id):
    if 'user_id' not in session or not is_admin():
        return redirect('/login')

    db = get_db()
    db.execute('DELETE FROM support WHERE id = ?', (ticket_id,))
    db.commit()
    return redirect('/admin')

@app.route('/admin/delete_stock/<symbol>')
def delete_stock(symbol):
    if 'user_id' not in session or not is_admin():
        return redirect('/login')

    db = get_db()
    db.execute('DELETE FROM stock_list WHERE symbol = ?', (symbol,))
    db.commit()
    return redirect('/admin')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    # Simulate index values
    def simulate_index(base):
        delta = random.uniform(-200, 200)
        value = round(base + delta, 2)
        change = round((delta / base) * 100, 2)
        return {
            "value": value,
            "change": change,
            "is_up": change >= 0
        }

    indices = {
        "Sensex": simulate_index(51800),
        "Nifty": simulate_index(15800),
        "BankNifty": simulate_index(34800),
        "Midcap": simulate_index(25200),
    }

    # Fetch recent transactions (5 latest for user)
    transactions = db.execute(
        'SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT 5',
        (session['user_id'],)
    ).fetchall()

    # Simulate chart data (based on Sensex-like behavior)
    base_price = 51800
    chart_data = []
    for _ in range(50):
        base_price += random.uniform(-200, 1    )
        chart_data.append(round(base_price, 2))
    chart_labels = [f"{i}" for i in range(1, 51)]

    # Mock stock screener (static for now)
    screener = [
        {"name": "Reliance", "price": 211.75, "change": 1.22, "volume": "758.54K", "sector": "Energy"},
        {"name": "Infosys", "price": 501.28, "change": 3.58, "volume": "987.36K", "sector": "Tech"},
        {"name": "HDFC", "price": 167.84, "change": 5.88, "volume": "125.59K", "sector": "Finance"},
        {"name": "SBIN", "price": 499.36, "change": 1.89, "volume": "584.35K", "sector": "Finance"},
        {"name": "Titan", "price": 296.89, "change": 4.12, "volume": "650.49K", "sector": "Consumer"}
    ]

    return render_template(
        'dashboard.html',
        user=user,
        indices=indices,
        transactions=transactions,
        chart_data=chart_data,
        chart_labels=chart_labels,
        screener=screener
    )

@app.route('/api/indices')
def get_indices():
    def simulate_index(base):
        delta = random.uniform(-200, 200)
        value = round(base + delta, 2)
        change = round((delta / base) * 100, 2)
        return {
            "value": value,
            "change": change,
            "is_up": change >= 0
        }

    indices = { 
        "Sensex": simulate_index(51800),
        "Nifty": simulate_index(15800),
        "BankNifty": simulate_index(34800),
        "Midcap": simulate_index(25200),
    }
    return jsonify(indices)


@app.route('/market')
def market():
    if 'user_id' not in session:
        return redirect('/login')
    
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    stocks_list = []

    # 1. Include hardcoded stocks
    for symbol, base_price in stocks.items():
        price = round(base_price * random.uniform(0.98, 1.02), 2)
        change = round(random.uniform(-2, 2), 2)
        trend = [round(price * random.uniform(0.98, 1.02), 2) for _ in range(10)]
        high = max(trend)
        low = min(trend)
        sentiment = random.choice(["Bullish", "Bearish", "Neutral"])

        stocks_list.append({
            'symbol': symbol,
            'price': price,
            'change': change,
            'trend': trend,
            'high': high,
            'low': low,
            'sentiment': sentiment
        })

    # 2. Include admin-added stocks from database
    stock_rows = db.execute('SELECT * FROM stock_list').fetchall()
    for row in stock_rows:
        price = round(row['price'] * random.uniform(0.98, 1.02), 2)
        change = round(random.uniform(-2, 2), 2)
        trend = [round(price * random.uniform(0.98, 1.02), 2) for _ in range(10)]

        stocks_list.append({
            'symbol': row['symbol'],
            'price': price,
            'change': change,
            'trend': trend,
            'high': row['high'],
            'low': row['low'],
            'sentiment': row['sentiment']
        })

    return render_template('market.html', user=user, stocks=stocks_list)



@app.route('/buy/<symbol>', methods=['POST'])
def buy(symbol):
    if 'user_id' not in session: return redirect('/login')
    qty = int(request.form['quantity'])
    price = float(request.form['price'])
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    cost = qty * price
    if user['balance'] >= cost:
        db.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (cost, user['id']))
        existing = db.execute('SELECT * FROM portfolio WHERE user_id = ? AND stock_symbol = ?', (user['id'], symbol)).fetchone()
        if existing:
            total_qty = existing['quantity'] + qty
            avg_price = (existing['avg_buy_price'] * existing['quantity'] + cost) / total_qty
            db.execute('UPDATE portfolio SET quantity = ?, avg_buy_price = ? WHERE id = ?', (total_qty, avg_price, existing['id']))
        else:
            db.execute('INSERT INTO portfolio (user_id, stock_symbol, quantity, avg_buy_price) VALUES (?, ?, ?, ?)', (user['id'], symbol, qty, price))
        db.execute('INSERT INTO transactions (user_id, stock_symbol, quantity, price, type, date) VALUES (?, ?, ?, ?, ?, ?)',
                   (user['id'], symbol, qty, price, 'BUY', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
    return redirect('/portfolio')


@app.route('/sell/<symbol>', methods=['POST'])
def sell(symbol):
    if 'user_id' not in session:
        return redirect('/login')

    qty_to_sell = int(request.form['quantity'])
    sell_price = float(request.form['price'])

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    holding = db.execute('SELECT * FROM portfolio WHERE user_id = ? AND stock_symbol = ?', 
                         (user['id'], symbol)).fetchone()

    if not holding or qty_to_sell > holding['quantity']:
        return redirect('/portfolio')  # Invalid quantity or no holdings

    total_income = qty_to_sell * sell_price

    # Update user's balance
    db.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (total_income, user['id']))

    # Update portfolio
    if qty_to_sell == holding['quantity']:
        db.execute('DELETE FROM portfolio WHERE id = ?', (holding['id'],))
    else:
        new_qty = holding['quantity'] - qty_to_sell
        db.execute('UPDATE portfolio SET quantity = ? WHERE id = ?', (new_qty, holding['id']))

    # Log transaction
    db.execute('''
        INSERT INTO transactions (user_id, stock_symbol, quantity, price, type, date)
        VALUES (?, ?, ?, ?, 'SELL', ?)
    ''', (user['id'], symbol, qty_to_sell, sell_price, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    db.commit()
    return redirect('/portfolio')


@app.route('/portfolio')
def portfolio():
    if 'user_id' not in session: return redirect('/login')
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    rows = db.execute('SELECT * FROM portfolio WHERE user_id = ?', (session['user_id'],)).fetchall()
    prices = {s: round(stocks[s] * random.uniform(0.98, 1.02), 2) for s in [row['stock_symbol'] for row in rows]}
    return render_template('portfolio.html', user=user, rows=rows, prices=prices)
    

@app.route('/transactions')
def transactions():
    if 'user_id' not in session: return redirect('/login')
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    rows = db.execute('SELECT * FROM transactions WHERE user_id = ?', (session['user_id'],)).fetchall()
    return render_template('transactions.html', user=user, rows=rows)


@app.route('/watchlist')
def watchlist():
    if 'user_id' not in session:
        return redirect('/login')
    db = get_db()
    watch = db.execute('SELECT stock_symbol FROM watchlist WHERE user_id = ?', (session['user_id'],)).fetchall()
    symbols = [row['stock_symbol'] for row in watch]
    prices = {s: round(stocks[s] * random.uniform(0.98, 1.02), 2) for s in symbols if s in stocks}
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('watchlist.html', watchlist=symbols, prices=prices, user=user)


@app.route('/add_watchlist/<symbol>', methods=['POST'])
def add_watchlist(symbol):
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user_id = session['user_id']

    # Check if already in watchlist
    exists = db.execute(
        'SELECT 1 FROM watchlist WHERE user_id = ? AND stock_symbol = ?',
        (user_id, symbol)
    ).fetchone()

    if not exists:
        db.execute(
            'INSERT INTO watchlist (user_id, stock_symbol) VALUES (?, ?)',
            (user_id, symbol)
        )
        db.commit()

    # Redirect to Watchlist page instead of staying on market
    return redirect('/watchlist')


@app.route('/remove_watchlist/<symbol>')
def remove_watchlist(symbol):
    if 'user_id' not in session:
        return redirect('/login')
    db = get_db()
    db.execute('DELETE FROM watchlist WHERE user_id = ? AND stock_symbol = ?', (session['user_id'], symbol))
    db.commit()
    return redirect('/watchlist')


@app.route('/prediction')
def prediction():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    predictions = {}

    for symbol, base_price in stocks.items():
        history = simulate_stock_history(base_price, symbol)
        live, predicted, profit = get_prediction_from_history(history)

        predictions[symbol] = {
            'live': live,
            'predicted': predicted,
            'profit': profit
        }

    return render_template('prediction.html', predictions=predictions, user=user)


@app.route('/buy_prediction/<symbol>', methods=['POST'])
def buy_prediction(symbol):
    if 'user_id' not in session: return redirect('/login')
    request.form = request.form.copy()
    request.form['price'] = float(request.form['price'])
    return buy(symbol)


@app.route('/support', methods=['GET', 'POST'])
def support():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()

    if request.method == 'POST':
        subject = request.form['subject']
        message = request.form['message']
        user_id = session['user_id']
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        db.execute('''
            INSERT INTO support (user_id, subject, message, date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, subject, message, date))
        db.commit()

        return redirect('/support')  # redirect to avoid form resubmission

    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('support.html', user=user)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    message = None

    if request.method == 'POST':
        current_pw = request.form['current_password']
        new_pw = request.form['new_password']
        confirm_pw = request.form['confirm_password']

        def is_strong(password):
            return (
                len(password) >= 8 and
                re.search(r"[A-Z]", password) and
                re.search(r"[a-z]", password) and
                re.search(r"[0-9]", password) and
                re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
            )

        if not check_password_hash(user['password'], current_pw):
            message = "❌ Current password is incorrect."
        elif new_pw != confirm_pw:
            message = "❌ New password and confirmation do not match."
        elif not is_strong(new_pw):
            message = "❌ Password must be at least 8 characters and include uppercase, lowercase, number, and special character."
        else:
            hashed_pw = generate_password_hash(new_pw)
            db.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, user['id']))
            db.commit()
            message = "✅ Password updated successfully."
            user = db.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()

    return render_template('settings.html', user=user, message=message)


@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    message = None
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user:
            code = str(random.randint(100000, 999999))  # ← defined here
            db.execute('UPDATE users SET reset_code = ? WHERE email = ?', (code, email))
            db.commit()

            # ✅ This part must come AFTER code is defined
            msg = MIMEText(f"Your OTP code is: {code}")
            msg['Subject'] = "TradeHaven Password Reset Code"
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = email

            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.starttls()
                    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                    smtp.send_message(msg)
                return redirect('/verify')
            except Exception as e:
                print("❌ SMTP ERROR:", e)
                message = "❌ Failed to send email. Try again later."
        else:
            message = "❌ Email not found."

    return render_template('forgot.html', message=message)



@app.route('/verify', methods=['GET', 'POST'])
def verify_code():
    message = None
    if request.method == 'POST':
        otp = request.form['otp']
        new_password = request.form['new_password']

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE reset_code = ?', (otp,)).fetchone()

        if user:
            hashed_pw = generate_password_hash(new_password)
            db.execute('UPDATE users SET password = ?, reset_code = NULL WHERE id = ?', (hashed_pw, user['id']))
            db.commit()
            message = "✅ Password reset successful. You can now log in."
            return redirect('/login')
        else:
            message = "❌ Invalid or expired code."

    return render_template('verify_reset.html', message=message)




@app.route('/download_transactions')
def download_transactions():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    cursor = get_db().cursor()
    cursor.execute('''
        SELECT date, type, stock_symbol, quantity, price
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC
    ''', (user_id,))
    rows = cursor.fetchall()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Type', 'Stock', 'Quantity', 'Price (₹)'])
    for row in rows:
        writer.writerow([row['date'], row['type'], row['stock_symbol'], row['quantity'], row['price']])
    
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='transactions.csv')


if __name__ == '__main__':
    init_db()  # manual DB init to avoid before_first_request issue
    app.run(debug=True)
    