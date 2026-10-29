"""
Bank Management System - Complete Application
"""
from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import random

# ========== INITIALIZE APP ==========
app = Flask(__name__)
app.secret_key = 'bank-management-system-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========== DATABASE MODELS ==========
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    user_type = db.Column(db.String(10), default='customer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    accounts = db.relationship('BankAccount', backref='user', lazy=True, cascade='all, delete-orphan')
    loans = db.relationship('Loan', backref='user', lazy=True, cascade='all, delete-orphan')

class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    account_type = db.Column(db.String(20), default='Savings')
    balance = db.Column(db.Float, default=0.00)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship('Transaction', backref='account', lazy=True, cascade='all, delete-orphan')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id', ondelete='CASCADE'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    to_account = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Loan(db.Model):
    __tablename__ = 'loans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    term = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.Text)
    employment = db.Column(db.String(50))
    income = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)

# ========== HELPERS ==========
def generate_account_number():
    while True:
        acc = 'BANK' + ''.join([str(random.randint(0, 9)) for _ in range(10)])
        if not BankAccount.query.filter_by(account_number=acc).first():
            return acc

def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('user_type') == 'admin'

# ========== GENERAL ROUTES ==========
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        flash(f'Thank you {name}! We will contact you soon.', 'success')
        return redirect('/contact')
    return render_template('contact.html')

# ========== AUTH ROUTES ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_type'] = user.user_type
            session['full_name'] = user.full_name
            flash(f'Welcome back, {user.full_name}!', 'success')
            if user.user_type == 'admin':
                return redirect('/admin/dashboard')
            return redirect('/customer/dashboard')
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        full_name = request.form['full_name']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect('/register')
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect('/register')
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect('/register')

        new_user = User(
            username=username,
            password=generate_password_hash(password),
            email=email,
            full_name=full_name,
            phone=phone,
            address=address,
            user_type='customer'
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            flash(f'Password reset link sent to {email}', 'info')
        else:
            flash('Email not found!', 'error')
        return redirect('/login')
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect('/')

# ========== PROFILE ==========
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.phone = request.form['phone']
        user.address = request.form['address']
        user.email = request.form['email']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect('/profile')
    return render_template('profile.html', user=user)

# ========== ADMIN ROUTES ==========
@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_logged_in() or not is_admin():
        flash('Admin login required!', 'error')
        return redirect('/login')

    total_users = User.query.count()
    total_accounts = BankAccount.query.count()
    total_balance = db.session.query(db.func.sum(BankAccount.balance)).scalar() or 0
    pending_loans = Loan.query.filter_by(status='Pending').count()
    users = User.query.all()
    loans = Loan.query.order_by(Loan.applied_date.desc()).all()

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_accounts=total_accounts,
                           total_balance=total_balance,
                           pending_loans=pending_loans,
                           users=users,
                           loans=loans)

@app.route('/admin/approve-loan/<int:loan_id>', methods=['POST'])
def approve_loan(loan_id):
    if not is_logged_in() or not is_admin():
        flash('Admin access required!', 'error')
        return redirect('/login')
    loan = Loan.query.get_or_404(loan_id)
    loan.status = 'Approved'
    db.session.commit()
    flash(f'Loan of ₹{loan.amount:,.2f} approved!', 'success')
    return redirect('/admin/dashboard')

@app.route('/admin/reject-loan/<int:loan_id>', methods=['POST'])
def reject_loan(loan_id):
    if not is_logged_in() or not is_admin():
        flash('Admin access required!', 'error')
        return redirect('/login')
    loan = Loan.query.get_or_404(loan_id)
    loan.status = 'Rejected'
    db.session.commit()
    flash('Loan application rejected!', 'info')
    return redirect('/admin/dashboard')

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if not is_logged_in() or not is_admin():
        flash('Admin access required!', 'error')
        return redirect('/login')
    user = User.query.get(user_id)
    if user and user.username != 'admin':
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} deleted successfully!', 'success')
    else:
        flash('Cannot delete admin user!', 'error')
    return redirect('/admin/dashboard')

# ========== CUSTOMER ROUTES ==========
@app.route('/customer/dashboard')
def customer_dashboard():
    if not is_logged_in() or session.get('user_type') != 'customer':
        flash('Please login first!', 'error')
        return redirect('/login')
    user = User.query.get(session['user_id'])
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    loans = Loan.query.filter_by(user_id=session['user_id']).order_by(Loan.applied_date.desc()).all()
    account_ids = [acc.id for acc in accounts]
    recent_transactions = Transaction.query.filter(
        Transaction.account_id.in_(account_ids)
    ).order_by(Transaction.date.desc()).limit(5).all() if account_ids else []
    return render_template('customer_dashboard.html',
                           user=user,
                           accounts=accounts,
                           loans=loans,
                           recent_transactions=recent_transactions)

@app.route('/dashboard')
def dashboard():
    return redirect('/customer/dashboard')

@app.route('/balance')
def balance():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    return render_template('balance.html', accounts=accounts)

@app.route('/statement')
def statement():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    account_ids = [acc.id for acc in accounts]
    transactions = Transaction.query.filter(
        Transaction.account_id.in_(account_ids)
    ).order_by(Transaction.date.desc()).all()
    return render_template('statement.html', transactions=transactions)

@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    if request.method == 'POST':
        account_type = request.form['account_type']
        initial_deposit = float(request.form.get('initial_deposit', 0))
        new_account = BankAccount(
            user_id=session['user_id'],
            account_number=generate_account_number(),
            account_type=account_type,
            balance=initial_deposit
        )
        db.session.add(new_account)
        db.session.flush()
        if initial_deposit > 0:
            tx = Transaction(
                account_id=new_account.id,
                transaction_type='Deposit',
                amount=initial_deposit,
                description='Initial deposit'
            )
            db.session.add(tx)
        db.session.commit()
        flash(f'Account created! Account: {new_account.account_number}', 'success')
        return redirect('/customer/dashboard')
    return render_template('create_account.html')

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    if request.method == 'POST':
        account_id = request.form['account_id']
        amount = float(request.form['amount'])
        description = request.form.get('description', 'Cash Deposit')
        account = BankAccount.query.get(account_id)
        if account and account.user_id == session['user_id']:
            account.balance += amount
            tx = Transaction(account_id=account_id,
                             transaction_type='Deposit',
                             amount=amount,
                             description=description)
            db.session.add(tx)
            db.session.commit()
            flash(f'Deposited ₹{amount:,.2f} successfully!', 'success')
            return redirect('/customer/dashboard')
        flash('Invalid account!', 'error')
    return render_template('deposit.html', accounts=accounts)

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    if request.method == 'POST':
        account_id = request.form['account_id']
        amount = float(request.form['amount'])
        description = request.form.get('description', 'Cash Withdrawal')
        account = BankAccount.query.get(account_id)
        if account and account.user_id == session['user_id']:
            if account.balance >= amount:
                account.balance -= amount
                tx = Transaction(account_id=account_id,
                                 transaction_type='Withdrawal',
                                 amount=amount,
                                 description=description)
                db.session.add(tx)
                db.session.commit()
                flash(f'Withdrew ₹{amount:,.2f} successfully!', 'success')
                return redirect('/customer/dashboard')
            flash('Insufficient balance!', 'error')
        else:
            flash('Invalid account!', 'error')
    return render_template('withdraw.html', accounts=accounts)

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
    if request.method == 'POST':
        from_account_id = request.form['from_account']
        to_account_number = request.form['to_account']
        amount = float(request.form['amount'])
        description = request.form.get('description', 'Fund Transfer')

        from_account = BankAccount.query.get(from_account_id)
        to_account = BankAccount.query.filter_by(account_number=to_account_number).first()

        if not from_account or from_account.user_id != session['user_id']:
            flash('Invalid source account!', 'error')
        elif not to_account:
            flash('Receiver account not found!', 'error')
        elif from_account.account_number == to_account_number:
            flash('Cannot transfer to same account!', 'error')
        elif from_account.balance < amount:
            flash('Insufficient balance!', 'error')
        else:
            from_account.balance -= amount
            to_account.balance += amount

            sender_tx = Transaction(
                account_id=from_account_id,
                transaction_type='Transfer',
                amount=amount,
                description=f'Transfer to {to_account_number}: {description}',
                to_account=to_account_number
            )
            receiver_tx = Transaction(
                account_id=to_account.id,
                transaction_type='Deposit',
                amount=amount,
                description=f'Transfer from {from_account.account_number}: {description}'
            )
            db.session.add(sender_tx)
            db.session.add(receiver_tx)
            db.session.commit()
            flash(f'Transferred ₹{amount:,.2f} to {to_account_number}', 'success')
            return redirect('/customer/dashboard')
    return render_template('transfer.html', accounts=accounts)

@app.route('/transactions')
def transactions():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    account_id = request.args.get('account_id')
    if account_id:
        transactions_list = Transaction.query.filter_by(account_id=account_id)\
            .order_by(Transaction.date.desc()).all()
        account = BankAccount.query.get(account_id)
        account_info = f"{account.account_number} ({account.account_type})" if account else "All Accounts"
    else:
        accounts = BankAccount.query.filter_by(user_id=session['user_id']).all()
        account_ids = [acc.id for acc in accounts]
        transactions_list = Transaction.query.filter(
            Transaction.account_id.in_(account_ids)
        ).order_by(Transaction.date.desc()).all()
        account_info = "All Accounts"
    return render_template('transactions.html',
                           transactions=transactions_list,
                           account_info=account_info)

@app.route('/loan', methods=['GET', 'POST'])
def loan():
    if not is_logged_in():
        flash('Please login to apply for loan!', 'error')
        return redirect('/login')
    if request.method == 'POST':
        new_loan = Loan(
            user_id=session['user_id'],
            loan_type=request.form['loan_type'],
            amount=float(request.form['amount']),
            term=int(request.form['term']),
            purpose=request.form['purpose'],
            employment=request.form['employment'],
            income=float(request.form['income']),
            status='Pending'
        )
        db.session.add(new_loan)
        db.session.commit()
        flash('Loan application submitted! We will review within 24 hours.', 'success')
        return redirect('/customer/dashboard')
    return render_template('loan.html')

@app.route('/notifications')
def notifications():
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    return render_template('notifications.html')

# ========== DELETE ACCOUNT ==========
@app.route('/delete-account/<int:account_id>', methods=['GET', 'POST'])
def delete_account(account_id):
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    account = BankAccount.query.get_or_404(account_id)
    if account.user_id != session['user_id']:
        flash('Unauthorized access!', 'error')
        return redirect('/customer/dashboard')
    if request.method == 'POST':
        if account.balance > 0:
            flash('Please withdraw all money before deleting account!', 'error')
            return redirect(url_for('withdraw'))
        db.session.delete(account)
        db.session.commit()
        flash('Account deleted successfully!', 'success')
        return redirect('/customer/dashboard')
    return render_template('delete_account.html', account=account)

@app.route('/confirm-delete/<int:account_id>')
def confirm_delete(account_id):
    if not is_logged_in():
        flash('Please login first!', 'error')
        return redirect('/login')
    account = BankAccount.query.get_or_404(account_id)
    if account.user_id != session['user_id']:
        flash('Unauthorized access!', 'error')
        return redirect('/customer/dashboard')
    return render_template('confirm_delete.html', account=account)

# ========== ERROR ==========
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# ========== INIT DB ==========
def init_database():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@bank.com',
                full_name='System Administrator',
                user_type='admin'
            )
            db.session.add(admin)
            db.session.flush()
            admin_acc = BankAccount(
                user_id=admin.id,
                account_number='ADMIN001',
                account_type='Current',
                balance=1000000.00
            )
            db.session.add(admin_acc)
            db.session.commit()
            print("✅ Admin created: admin / admin123")

# ========== RUN ==========
if __name__ == '__main__':
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    init_database()
    print("\n" + "="*60)
    print("🏦 BANK MANAGEMENT SYSTEM STARTED")
    print("="*60)
    print("🌐 Server: http://127.0.0.1:5000")
    print("👑 Admin: admin / admin123")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)