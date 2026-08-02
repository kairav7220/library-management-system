from flask import Flask, jsonify, render_template, request, redirect, url_for
from datetime import datetime
from dotenv import load_dotenv
import gspread
import os
import json
from google.oauth2.service_account import Credentials

load_dotenv()

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets'
]

creds_json = os.environ.get('GOOGLE_CREDENTIALS')
if creds_json:
    creds_dict = json.loads(creds_json)
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
else:
    credentials = Credentials.from_service_account_file('credentials.json', scopes=scope)

gc = gspread.authorize(credentials)

sheet = gc.open_by_key(os.getenv('GOOGLE_SHEET_ID'))
user_worksheet = sheet.worksheet('User Table')
book_worksheet = sheet.worksheet('Book Table')
book_category_ws = sheet.worksheet('Book Category')
book_genre_ws = sheet.worksheet('Book Genre')
member_worksheet = sheet.worksheet('Member Table')
employee_worksheet = sheet.worksheet('Employee Table')
subscription_worksheet = sheet.worksheet('Subscription Table')
payment_worksheet =  sheet.worksheet('Payment Table')
book_sell_worksheet = sheet.worksheet('Book Sell')
book_issue_worksheet = sheet.worksheet('Book Issue')

app = Flask(__name__)

# ─── Users ───────────────────────────────────────────────

@app.route('/')
def index():
    all_values = user_worksheet.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        if row[7] == '0':
            rows.append({'data': row, 'sheet_row': i})
    return render_template('index.html', headers=headers, rows=rows)

@app.route('/list')
def get_all_users():
    all_values = user_worksheet.get_all_values()
    return jsonify({'sheet_data': all_values})

@app.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        all_values = user_worksheet.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="USER_"&A{next_row}-1', user_type, username, password, email, phone, '0']
        user_worksheet.update([row_data], f'A{next_row}:H{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('index'))
    return render_template('add_user.html')

@app.route('/update/<int:row_num>', methods=['GET', 'POST'])
def update_user(row_num):
    if request.method == 'POST':
        password = request.form.get('password')
        phone = request.form.get('phone')
        user_worksheet.update_acell(f'E{row_num}', password)
        user_worksheet.update_acell(f'G{row_num}', phone)
        return redirect(url_for('index'))

    user_row = user_worksheet.get(f'A{row_num}:J{row_num}')[0]
    return render_template('form.html', user=user_row, row_num=row_num)

@app.route('/delete/<int:row_num>')
def delete_user(row_num):
    user_worksheet.update_acell(f'H{row_num}', '1')
    return redirect(url_for('index'))

# ─── Books ───────────────────────────────────────────────

@app.route('/books')
def books():
    all_values = book_worksheet.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        if row[9] == '0':
            rows.append({'data': row, 'sheet_row': i})
    return render_template('books.html', headers=headers, rows=rows)

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book_name = request.form.get('book_name')
        book_author = request.form.get('book_author')
        book_price = request.form.get('book_price')
        book_cat = request.form.get('book_cat')
        book_genre = request.form.get('book_genre')
        edition = request.form.get('edition')
        publication = request.form.get('publication')
        all_values = book_worksheet.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="BOOK_"&A{next_row}-1', book_name, book_author, book_price, book_cat, book_genre, edition, publication, '0']
        book_worksheet.update([row_data], f'A{next_row}:J{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('books'))
    return render_template('add_book.html')

@app.route('/books/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_book(row_num):
    if request.method == 'POST':
        book_worksheet.update_acell(f'C{row_num}', request.form.get('book_name'))
        book_worksheet.update_acell(f'D{row_num}', request.form.get('book_author'))
        book_worksheet.update_acell(f'E{row_num}', request.form.get('book_price'))
        book_worksheet.update_acell(f'F{row_num}', request.form.get('book_cat'))
        book_worksheet.update_acell(f'G{row_num}', request.form.get('book_genre'))
        book_worksheet.update_acell(f'H{row_num}', request.form.get('edition'))
        book_worksheet.update_acell(f'I{row_num}', request.form.get('publication'))
        return redirect(url_for('books'))

    book_row = book_worksheet.get(f'A{row_num}:J{row_num}')[0]
    return render_template('edit_book.html', book=book_row, row_num=row_num)

@app.route('/books/delete/<int:row_num>')
def delete_book(row_num):
    book_worksheet.update_acell(f'J{row_num}', '1')
    return redirect(url_for('books'))

# ─── Book Category ───────────────────────────────────────────────

@app.route('/book_cat')
def book_category():
    all_values = book_category_ws.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        if row[5] == '0':
            rows.append({'data': row, 'sheet_row': i})
    return render_template('book_category.html', headers=headers, rows=rows)

@app.route('/book_cat/add', methods=['GET', 'POST'])
def add_book_category():
    if request.method == 'POST':
        cat_name = request.form.get('cat_name')
        description = request.form.get('description')
        book_names = request.form.get('book_names')
        all_values = book_category_ws.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="CAT_"&A{next_row}-1', cat_name, description, book_names, '0']
        book_category_ws.update([row_data], f'A{next_row}:F{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('book_category'))
    return render_template('add_book_category.html')

@app.route('/book_cat/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_book_category(row_num):
    if request.method == 'POST':
        book_category_ws.update_acell(f'C{row_num}', request.form.get('cat_name'))
        book_category_ws.update_acell(f'D{row_num}', request.form.get('description'))
        book_category_ws.update_acell(f'E{row_num}', request.form.get('book_names'))
        return redirect(url_for('book_category'))

    book_cat_row = book_category_ws.get(f'A{row_num}:F{row_num}')[0]
    return render_template('edit_book_category.html', book_cat=book_cat_row, row_num=row_num)

@app.route('/book_cat/delete/<int:row_num>')
def delete_book_category(row_num):
    book_category_ws.update_acell(f'F{row_num}', '1')
    return redirect(url_for('book_category'))

# ─── Book Genre ───────────────────────────────────────────────

@app.route('/book_genre')
def book_genre():
    all_values = book_genre_ws.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        if row[4] == '0':
            rows.append({'data': row, 'sheet_row': i})
    return render_template('book_genre.html', headers=headers, rows=rows)

@app.route('/book_genre/add', methods=['GET', 'POST'])
def add_book_genre():
    if request.method == 'POST':
        genre_title = request.form.get('genre_title')
        book_names = request.form.get('book_names')
        all_values = book_genre_ws.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="GENRE_"&A{next_row}-1', genre_title, book_names, '0']
        book_genre_ws.update([row_data], f'A{next_row}:E{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('book_genre'))
    return render_template('add_book_genre.html')

@app.route('/book_genre/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_book_genre(row_num):
    if request.method == 'POST':
        book_genre_ws.update_acell(f'C{row_num}', request.form.get('genre_title'))
        book_genre_ws.update_acell(f'D{row_num}', request.form.get('book_names'))
        return redirect(url_for('book_genre'))

    genre_row = book_genre_ws.get(f'A{row_num}:E{row_num}')[0]
    return render_template('edit_book_genre.html', genre=genre_row, row_num=row_num)

@app.route('/book_genre/delete/<int:row_num>')
def delete_book_genre(row_num):
    book_genre_ws.update_acell(f'E{row_num}', '1')
    return redirect(url_for('book_genre'))

# ─── Members ───────────────────────────────────────────────

@app.route('/members')
def members():
    all_values = member_worksheet.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        if row[10] == '0':
            rows.append({'data': row, 'sheet_row': i})
    return render_template('members.html', headers=headers, rows=rows)

@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        permanent_address = request.form.get('permanent_address')
        temporary_address = request.form.get('temporary_address')
        all_values = member_worksheet.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="MEM_"&A{next_row}-1', name, user_id, password, email, phone, '', permanent_address, temporary_address, '0']
        member_worksheet.update([row_data], f'A{next_row}:K{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('members'))
    return render_template('add_member.html')

@app.route('/members/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_member(row_num):
    if request.method == 'POST':
        member_worksheet.update_acell(f'C{row_num}', request.form.get('name'))
        member_worksheet.update_acell(f'D{row_num}', request.form.get('user_id'))
        member_worksheet.update_acell(f'E{row_num}', request.form.get('password'))
        member_worksheet.update_acell(f'F{row_num}', request.form.get('email'))
        member_worksheet.update_acell(f'G{row_num}', request.form.get('phone'))
        member_worksheet.update_acell(f'I{row_num}', request.form.get('permanent_address'))
        member_worksheet.update_acell(f'J{row_num}', request.form.get('temporary_address'))
        return redirect(url_for('members'))

    member_row = member_worksheet.get(f'A{row_num}:K{row_num}')[0]
    return render_template('edit_member.html', member=member_row, row_num=row_num)

@app.route('/members/delete/<int:row_num>')
def delete_member(row_num):
    member_worksheet.update_acell(f'K{row_num}', '1')
    return redirect(url_for('members'))

# ─── Employees ───────────────────────────────────────────────

@app.route('/employees')
def employees():
    all_values = employee_worksheet.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        if row[12] == '0':
            rows.append({'data': row, 'sheet_row': i})
    return render_template('employees.html', headers=headers, rows=rows)

@app.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        name = request.form.get('name')
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        designation = request.form.get('designation')
        salary = request.form.get('salary')
        permanent_address = request.form.get('permanent_address')
        temporary_address = request.form.get('temporary_address')
        all_values = employee_worksheet.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="EMP_"&A{next_row}-1', name, user_id, password, email, phone, designation, salary, '', permanent_address, temporary_address, '0']
        employee_worksheet.update([row_data], f'A{next_row}:M{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('employees'))
    return render_template('add_employee.html')

@app.route('/employees/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_employee(row_num):
    if request.method == 'POST':
        employee_worksheet.update_acell(f'C{row_num}', request.form.get('name'))
        employee_worksheet.update_acell(f'D{row_num}', request.form.get('user_id'))
        employee_worksheet.update_acell(f'E{row_num}', request.form.get('password'))
        employee_worksheet.update_acell(f'F{row_num}', request.form.get('email'))
        employee_worksheet.update_acell(f'G{row_num}', request.form.get('phone'))
        employee_worksheet.update_acell(f'H{row_num}', request.form.get('designation'))
        employee_worksheet.update_acell(f'I{row_num}', request.form.get('salary'))
        employee_worksheet.update_acell(f'K{row_num}', request.form.get('permanent_address'))
        employee_worksheet.update_acell(f'L{row_num}', request.form.get('temporary_address'))
        return redirect(url_for('employees'))

    emp_row = employee_worksheet.get(f'A{row_num}:M{row_num}')[0]
    return render_template('edit_employee.html', employee=emp_row, row_num=row_num)

@app.route('/employees/delete/<int:row_num>')
def delete_employee(row_num):
    employee_worksheet.update_acell(f'M{row_num}', '1')
    return redirect(url_for('employees'))

# ─── Subscriptions ───────────────────────────────────────────────

@app.route('/subscriptions')
def subscriptions():
    all_values = subscription_worksheet.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        if row[10] == '0':
            rows.append({'data': row, 'sheet_row': i})

    member_data = member_worksheet.get_all_values()
    member_names = {}
    for r in member_data[1:]:
        if r[1]:
            member_names[r[1]] = r[2]

    return render_template('subscriptions.html', headers=headers, rows=rows, member_names=member_names)

@app.route('/subscriptions/add', methods=['GET', 'POST'])
def add_subscription():
    if request.method == 'POST':
        plan_mode = request.form.get('plan_mode')
        mem_id = request.form.get('mem_id')
        mem_subscription_amount = request.form.get('mem_subscription_amount')
        plan_type = request.form.get('plan_type')
        plan_start = request.form.get('plan_start')
        plan_end = request.form.get('plan_end')
        all_values = subscription_worksheet.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="TXN_"&A{next_row}-1', datetime.now().strftime('%d-%b-%Y'), datetime.now().strftime('%I:%M:%S %p'), plan_mode, mem_id, mem_subscription_amount, plan_type, plan_start, plan_end, '0']
        subscription_worksheet.update([row_data], f'A{next_row}:K{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('subscriptions'))
    return render_template('add_subscription.html')

@app.route('/subscriptions/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_subscription(row_num):
    if request.method == 'POST':
        subscription_worksheet.update_acell(f'C{row_num}', request.form.get('transaction_date'))
        subscription_worksheet.update_acell(f'D{row_num}', request.form.get('timestamp'))
        subscription_worksheet.update_acell(f'E{row_num}', request.form.get('plan_mode'))
        subscription_worksheet.update_acell(f'F{row_num}', request.form.get('mem_id'))
        subscription_worksheet.update_acell(f'G{row_num}', request.form.get('mem_subscription_amount'))
        subscription_worksheet.update_acell(f'H{row_num}', request.form.get('plan_type'))
        subscription_worksheet.update_acell(f'I{row_num}', request.form.get('plan_start'))
        subscription_worksheet.update_acell(f'J{row_num}', request.form.get('plan_end'))
        subscription_worksheet.update_acell(f'K{row_num}', request.form.get('subscription_status'))
        return redirect(url_for('subscriptions'))

    sub_row = subscription_worksheet.get(f'A{row_num}:K{row_num}')[0]
    return render_template('edit_subscription.html', subscription=sub_row, row_num=row_num)

@app.route('/subscriptions/delete/<int:row_num>')
def delete_subscription(row_num):
    subscription_worksheet.update_acell(f'K{row_num}', '1')
    return redirect(url_for('subscriptions'))

# ─── Payments ───────────────────────────────────────────────

@app.route('/payments')
def payments():
    all_values = payment_worksheet.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        rows.append({'data': row, 'sheet_row': i})

    member_data = member_worksheet.get_all_values()
    member_names = {}
    for r in member_data[1:]:
        if r[1]:
            member_names[r[1]] = r[2]

    employee_data = employee_worksheet.get_all_values()
    employee_names = {}
    for r in employee_data[1:]:
        if r[1]:
            employee_names[r[1]] = r[2]

    return render_template('payments.html', headers=headers, rows=rows, member_names=member_names, employee_names=employee_names)

@app.route('/payments/add', methods=['GET', 'POST'])
def add_payment():
    if request.method == 'POST':
        payment_amount = request.form.get('payment_amount')
        payment_type = request.form.get('payment_type')
        payment_mode = request.form.get('payment_mode')
        payment_status = request.form.get('payment_status')
        paid_by = request.form.get('paid_by')
        recieved_by = request.form.get('recieved_by')
        all_values = payment_worksheet.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="TXN_"&A{next_row}-1', datetime.now().strftime('%d-%b-%Y'), datetime.now().strftime('%I:%M:%S %p'), payment_amount, payment_type, payment_mode, payment_status, paid_by, recieved_by, '']
        payment_worksheet.update([row_data], f'A{next_row}:K{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('payments'))
    return render_template('add_payment.html')

# ─── Book Sells ───────────────────────────────────────────────

@app.route('/book_sell')
def book_sell():
    all_values = book_sell_worksheet.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        rows.append({'data': row, 'sheet_row': i})

    member_data = member_worksheet.get_all_values()
    member_names = {}
    for r in member_data[1:]:
        if r[1]:
            member_names[r[1]] = r[2]

    return render_template('book_sell.html', headers=headers, rows=rows, member_names=member_names)

@app.route('/book_sell/add', methods=['GET', 'POST'])
def add_book_sell():
    if request.method == 'POST':
        order_date = request.form.get('order_date')
        book_id = request.form.get('book_id')
        book_name = request.form.get('book_name')
        book_price = request.form.get('book_price')
        mem_id = request.form.get('mem_id')
        all_values = book_sell_worksheet.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', f'="ORDER_"&A{next_row}-1', order_date, datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'), book_id, book_name, book_price, mem_id]
        book_sell_worksheet.update([row_data], f'A{next_row}:H{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('book_sell'))
    return render_template('add_book_sell.html')

@app.route('/book_sell/edit/<int:row_num>', methods=['GET', 'POST'])
def edit_book_sell(row_num):
    if request.method == 'POST':
        book_sell_worksheet.update_acell(f'C{row_num}', request.form.get('order_date'))
        book_sell_worksheet.update_acell(f'E{row_num}', request.form.get('book_id'))
        book_sell_worksheet.update_acell(f'F{row_num}', request.form.get('book_name'))
        book_sell_worksheet.update_acell(f'G{row_num}', request.form.get('book_price'))
        book_sell_worksheet.update_acell(f'H{row_num}', request.form.get('mem_id'))
        return redirect(url_for('book_sell'))

    sell_row = book_sell_worksheet.get(f'A{row_num}:H{row_num}')[0]
    return render_template('edit_book_sell.html', sell=sell_row, row_num=row_num)

# ─── Book Issues ───────────────────────────────────────────────

@app.route('/book_issue')
def book_issue():
    all_values = book_issue_worksheet.get_all_values()
    headers = all_values[0]
    rows = []
    for i, row in enumerate(all_values[1:], start=2):
        rows.append({'data': row, 'sheet_row': i})

    member_data = member_worksheet.get_all_values()
    member_names = {}
    for r in member_data[1:]:
        if r[1]:
            member_names[r[1]] = r[2]

    employee_data = employee_worksheet.get_all_values()
    employee_names = {}
    for r in employee_data[1:]:
        if r[1]:
            employee_names[r[1]] = r[2]

    book_data = book_worksheet.get_all_values()
    book_names = {}
    for r in book_data[1:]:
        if r[1]:
            book_names[r[1]] = r[2]

    return render_template('book_issue.html', headers=headers, rows=rows, member_names=member_names, employee_names=employee_names, book_names=book_names)

@app.route('/book_issue/add', methods=['GET', 'POST'])
def add_book_issue():
    if request.method == 'POST':
        transaction_id = request.form.get('transaction_id')
        transaction_date = request.form.get('transaction_date')
        book_id = request.form.get('book_id')
        issued_date = request.form.get('issued_date')
        issued_to = request.form.get('issued_to')
        all_values = book_issue_worksheet.get_all_values()
        next_row = len(all_values) + 1
        row_data = ['=ROW()', transaction_id, transaction_date, datetime.now().strftime('%d-%m-%Y %I:%M:%S %p'), book_id, issued_date, issued_to, '', '']
        book_issue_worksheet.update([row_data], f'A{next_row}:I{next_row}', value_input_option='USER_ENTERED')
        return redirect(url_for('book_issue'))
    return render_template('add_book_issue.html')

@app.route('/book_issue/return/<int:row_num>', methods=['GET', 'POST'])
def return_book_issue(row_num):
    if request.method == 'POST':
        book_issue_worksheet.update_acell(f'H{row_num}', request.form.get('received_by'))
        book_issue_worksheet.update_acell(f'I{row_num}', request.form.get('returned_date'))
        return redirect(url_for('book_issue'))

    issue_row = book_issue_worksheet.get(f'A{row_num}:I{row_num}')[0]
    return render_template('return_book_issue.html', issue=issue_row, row_num=row_num)

# ─── AI Assistant (multi-agent) ──────────────────────────

from graph.orchestrator import build_graph, build_classifier
from graph.memory import load_history, append_turn
from tools.llm import get_llm

_llm = get_llm()
_graph = build_graph(llm=_llm, classifier=build_classifier(_llm))


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    user_message = (data.get('message') or '').strip()
    session_id = data.get('session_id') or 'default'
    if not user_message:
        return jsonify({'response': 'Please type a message.'})

    history = load_history(session_id)
    messages = history + [{'role': 'user', 'content': user_message}]
    result = _graph.invoke({'messages': messages, 'session_id': session_id})

    response = None
    agent_name = None
    for m in result['messages']:
        if m.type == 'ai' and m.content:
            response = m.content
            agent_name = m.name
    response = response or 'I could not process that request.'

    append_turn(session_id, user_message, agent_name, response, [])
    return jsonify({'response': response, 'agent': agent_name})

if __name__ == '__main__':
    app.run(debug=True)