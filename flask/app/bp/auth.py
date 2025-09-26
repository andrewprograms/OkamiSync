from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.model.models import User, Role

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        pw = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(pw) and user.role == Role.user:
            login_user(user)
            next_url = request.args.get('next') or url_for('table.home')
            return redirect(next_url)
        flash('Invalid credentials or not a diner account.')
    return render_template('auth/login.html', role='user')

@bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        name = request.form['name'].strip()
        pw = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
        else:
            u = User(email=email, name=name, role=Role.user)
            u.set_password(pw)
            db.session.add(u)
            db.session.commit()
            login_user(u)
            return redirect(url_for('table.home'))
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('table.home'))

# Staff/Admin separate logins
@bp.route('/staff/login', methods=['GET','POST'])
def staff_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        pw = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(pw) and user.role == Role.staff:
            login_user(user)
            return redirect(url_for('staff.dashboard'))
        flash('Invalid staff credentials.')
    return render_template('auth/login.html', role='staff')

@bp.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        pw = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(pw) and user.role == Role.admin:
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid admin credentials.')
    return render_template('auth/login.html', role='admin')
