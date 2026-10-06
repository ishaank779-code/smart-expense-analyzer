from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, extract

from app import db
from app.models import User, Expense, Category, Budget
from app.forms import RegistrationForm, LoginForm, ExpenseForm, CategoryForm, BudgetForm

main = Blueprint('main', __name__)


# Default categories for new users
DEFAULT_CATEGORIES = [
    {'name': 'Food & Dining', 'icon': 'cup-hot', 'color': '#e74c3c'},
    {'name': 'Transportation', 'icon': 'car-front', 'color': '#3498db'},
    {'name': 'Shopping', 'icon': 'cart', 'color': '#9b59b6'},
    {'name': 'Bills & Utilities', 'icon': 'phone', 'color': '#f39c12'},
    {'name': 'Entertainment', 'icon': 'film', 'color': '#1abc9c'},
    {'name': 'Health', 'icon': 'heart-pulse', 'color': '#e91e63'},
    {'name': 'Education', 'icon': 'book', 'color': '#00bcd4'},
    {'name': 'Travel', 'icon': 'airplane', 'color': '#ff5722'},
    {'name': 'Salary/Income', 'icon': 'cash-stack', 'color': '#27ae60'},
    {'name': 'Other', 'icon': 'three-dots', 'color': '#95a5a6'},
]


def create_default_categories(user):
    for cat in DEFAULT_CATEGORIES:
        category = Category(
            name=cat['name'],
            icon=cat['icon'],
            color=cat['color'],
            user_id=user.id
        )
        db.session.add(category)
    db.session.commit()


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        create_default_categories(user)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@main.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    first_day = today.replace(day=1)
    
    # This month expenses
    month_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= first_day,
        Expense.date <= today
    ).all()
    
    total_spent = sum(float(e.amount) for e in month_expenses)
    
    # Category breakdown
    category_totals = defaultdict(float)
    category_colors = {}
    for exp in month_expenses:
        cat_name = exp.category.name
        category_totals[cat_name] += float(exp.amount)
        category_colors[cat_name] = exp.category.color
    
    # Recent expenses
    recent = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc(), Expense.created_at.desc()).limit(8).all()
    
    # Monthly trend (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        m_date = today.replace(day=1) - timedelta(days=30*i)
        m_start = m_date.replace(day=1)
        if m_date.month == 12:
            m_end = m_date.replace(year=m_date.year+1, month=1, day=1) - timedelta(days=1)
        else:
            m_end = m_date.replace(month=m_date.month+1, day=1) - timedelta(days=1)
        
        total = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= m_start,
            Expense.date <= m_end
        ).scalar()
        monthly_data.append({
            'month': m_start.strftime('%b %Y'),
            'total': float(total)
        })
    
    # Budget status
    current_budget = Budget.query.filter_by(
        user_id=current_user.id,
        category_id=None,
        month=today.month,
        year=today.year
    ).first()
    
    budget_amount = float(current_budget.amount) if current_budget else None
    budget_percent = (total_spent / budget_amount * 100) if budget_amount and budget_amount > 0 else None
    
    # Smart insights
    insights = generate_insights(current_user.id, month_expenses, total_spent, budget_amount)
    
    return render_template(
        'dashboard.html',
        total_spent=total_spent,
        category_totals=dict(category_totals),
        category_colors=category_colors,
        recent=recent,
        monthly_data=monthly_data,
        budget_amount=budget_amount,
        budget_percent=budget_percent,
        insights=insights,
        month_name=today.strftime('%B %Y')
    )


def generate_insights(user_id, month_expenses, total_spent, budget_amount):
    insights = []
    
    if not month_expenses:
        insights.append({
            'type': 'info',
            'icon': 'info-circle',
            'text': 'No expenses recorded this month. Start tracking to get smart insights!'
        })
        return insights
    
    # Highest category
    cat_totals = defaultdict(float)
    for e in month_expenses:
        cat_totals[e.category.name] += float(e.amount)
    
    if cat_totals:
        top_cat = max(cat_totals, key=cat_totals.get)
        top_amount = cat_totals[top_cat]
        pct = (top_amount / total_spent * 100) if total_spent > 0 else 0
        insights.append({
            'type': 'warning' if pct > 40 else 'info',
            'icon': 'pie-chart',
            'text': f'Highest spending is on <strong>{top_cat}</strong> (₹{top_amount:,.0f} — {pct:.0f}% of total).'
        })
    
    # Budget alert
    if budget_amount:
        remaining = budget_amount - total_spent
        if remaining < 0:
            insights.append({
                'type': 'danger',
                'icon': 'exclamation-triangle',
                'text': f'You have exceeded your monthly budget by ₹{abs(remaining):,.0f}!'
            })
        elif remaining < budget_amount * 0.2:
            insights.append({
                'type': 'warning',
                'icon': 'exclamation-circle',
                'text': f'Only ₹{remaining:,.0f} left in your budget this month. Spend carefully!'
            })
        else:
            insights.append({
                'type': 'success',
                'icon': 'check-circle',
                'text': f'You are within budget. ₹{remaining:,.0f} remaining for this month.'
            })
    
    # Average daily spend
    days_passed = date.today().day
    avg_daily = total_spent / days_passed if days_passed > 0 else 0
    insights.append({
        'type': 'info',
        'icon': 'calendar3',
        'text': f'Average daily spend this month: ₹{avg_daily:,.0f}'
    })
    
    # Payment method insight
    methods = defaultdict(float)
    for e in month_expenses:
        methods[e.payment_method] += float(e.amount)
    if methods:
        top_method = max(methods, key=methods.get)
        insights.append({
            'type': 'info',
            'icon': 'credit-card',
            'text': f'Most used payment method: <strong>{top_method}</strong>'
        })
    
    return insights


@main.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', type=int)
    search = request.args.get('search', '').strip()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Expense.query.filter_by(user_id=current_user.id)
    
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    if search:
        query = query.filter(Expense.title.ilike(f'%{search}%'))
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    
    pagination = query.order_by(Expense.date.desc(), Expense.created_at.desc())\
        .paginate(page=page, per_page=15, error_out=False)
    
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    
    return render_template(
        'expenses.html',
        expenses=pagination.items,
        pagination=pagination,
        categories=categories,
        category_filter=category_filter,
        search=search,
        start_date=start_date,
        end_date=end_date
    )


@main.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    form.category_id.choices = [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    ]
    
    if form.validate_on_submit():
        expense = Expense(
            title=form.title.data,
            amount=Decimal(str(form.amount.data)),
            category_id=form.category_id.data,
            date=form.date.data,
            payment_method=form.payment_method.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.expenses'))
    
    if request.method == 'GET':
        form.date.data = date.today()
    
    return render_template('expense_form.html', form=form, title='Add Expense')


@main.route('/expenses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.expenses'))
    
    form = ExpenseForm(obj=expense)
    form.category_id.choices = [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    ]
    
    if form.validate_on_submit():
        expense.title = form.title.data
        expense.amount = Decimal(str(form.amount.data))
        expense.category_id = form.category_id.data
        expense.date = form.date.data
        expense.payment_method = form.payment_method.data
        expense.description = form.description.data
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('main.expenses'))
    
    return render_template('expense_form.html', form=form, title='Edit Expense', expense=expense)


@main.route('/expenses/<int:id>/delete', methods=['POST'])
@login_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    if expense.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.expenses'))
    
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('main.expenses'))


@main.route('/categories')
@login_required
def categories():
    cats = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    # Count expenses per category
    cat_data = []
    for c in cats:
        count = Expense.query.filter_by(category_id=c.id).count()
        total = db.session.query(func.coalesce(func.sum(Expense.amount), 0))\
            .filter_by(category_id=c.id).scalar()
        cat_data.append({
            'category': c,
            'count': count,
            'total': float(total)
        })
    return render_template('categories.html', cat_data=cat_data)


@main.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        existing = Category.query.filter_by(
            name=form.name.data, user_id=current_user.id
        ).first()
        if existing:
            flash('Category with this name already exists.', 'danger')
        else:
            cat = Category(
                name=form.name.data,
                icon=form.icon.data,
                color=form.color.data,
                user_id=current_user.id
            )
            db.session.add(cat)
            db.session.commit()
            flash('Category created!', 'success')
            return redirect(url_for('main.categories'))
    return render_template('category_form.html', form=form, title='Add Category')


@main.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.categories'))
    
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        cat.name = form.name.data
        cat.icon = form.icon.data
        cat.color = form.color.data
        db.session.commit()
        flash('Category updated!', 'success')
        return redirect(url_for('main.categories'))
    return render_template('category_form.html', form=form, title='Edit Category')


@main.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    if cat.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.categories'))
    
    # Check if expenses exist
    if Expense.query.filter_by(category_id=cat.id).count() > 0:
        flash('Cannot delete category with existing expenses. Move or delete them first.', 'danger')
        return redirect(url_for('main.categories'))
    
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'success')
    return redirect(url_for('main.categories'))


@main.route('/budgets')
@login_required
def budgets():
    today = date.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    
    budgets_list = Budget.query.filter_by(
        user_id=current_user.id, year=year, month=month
    ).all()
    
    # Calculate spent for each
    budget_data = []
    for b in budgets_list:
        if b.category_id:
            spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
                Expense.user_id == current_user.id,
                Expense.category_id == b.category_id,
                extract('year', Expense.date) == year,
                extract('month', Expense.date) == month
            ).scalar()
            cat_name = b.category.name if b.category else 'Unknown'
        else:
            spent = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
                Expense.user_id == current_user.id,
                extract('year', Expense.date) == year,
                extract('month', Expense.date) == month
            ).scalar()
            cat_name = 'Overall Budget'
        
        budget_data.append({
            'budget': b,
            'category_name': cat_name,
            'spent': float(spent),
            'remaining': float(b.amount) - float(spent),
            'percent': min(100, float(spent) / float(b.amount) * 100) if float(b.amount) > 0 else 0
        })
    
    return render_template('budgets.html', budget_data=budget_data, year=year, month=month)


@main.route('/budgets/add', methods=['GET', 'POST'])
@login_required
def add_budget():
    form = BudgetForm()
    form.category_id.choices = [(0, 'Overall Budget')] + [
        (c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    ]
    
    today = date.today()
    if request.method == 'GET':
        form.month.data = today.month
        form.year.data = today.year
    
    if form.validate_on_submit():
        cat_id = form.category_id.data if form.category_id.data != 0 else None
        
        existing = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=cat_id,
            month=form.month.data,
            year=form.year.data
        ).first()
        
        if existing:
            existing.amount = Decimal(str(form.amount.data))
            db.session.commit()
            flash('Budget updated!', 'success')
        else:
            budget = Budget(
                category_id=cat_id,
                amount=Decimal(str(form.amount.data)),
                month=form.month.data,
                year=form.year.data,
                user_id=current_user.id
            )
            db.session.add(budget)
            db.session.commit()
            flash('Budget set successfully!', 'success')
        return redirect(url_for('main.budgets', year=form.year.data, month=form.month.data))
    
    return render_template('budget_form.html', form=form, title='Set Budget')


@main.route('/reports')
@login_required
def reports():
    today = date.today()
    year = request.args.get('year', today.year, type=int)
    
    # Monthly totals for the year
    monthly_totals = []
    for m in range(1, 13):
        total = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
            Expense.user_id == current_user.id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == m
        ).scalar()
        monthly_totals.append({
            'month': datetime(year, m, 1).strftime('%b'),
            'total': float(total)
        })
    
    # Category totals for the year
    cat_totals = db.session.query(
        Category.name,
        Category.color,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.user_id == current_user.id,
        extract('year', Expense.date) == year
    ).group_by(Category.id).order_by(func.sum(Expense.amount).desc()).all()
    
    category_data = [
        {'name': c[0], 'color': c[1], 'total': float(c[2])} for c in cat_totals
    ]
    
    # Payment method breakdown
    payment_totals = db.session.query(
        Expense.payment_method,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == current_user.id,
        extract('year', Expense.date) == year
    ).group_by(Expense.payment_method).all()
    
    payment_data = [
        {'method': p[0], 'total': float(p[1])} for p in payment_totals
    ]
    
    yearly_total = sum(m['total'] for m in monthly_totals)
    
    return render_template(
        'reports.html',
        year=year,
        monthly_totals=monthly_totals,
        category_data=category_data,
        payment_data=payment_data,
        yearly_total=yearly_total
    )


# API endpoints for charts (JSON)
@main.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    today = date.today()
    first_day = today.replace(day=1)
    
    month_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= first_day
    ).all()
    
    category_totals = defaultdict(float)
    for exp in month_expenses:
        category_totals[exp.category.name] += float(exp.amount)
    
    return jsonify({
        'categories': list(category_totals.keys()),
        'amounts': list(category_totals.values())
    })
