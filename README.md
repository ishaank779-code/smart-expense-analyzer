# Smart Expense Analyzer

A complete, production-ready web application for tracking personal expenses with smart insights, budgets, and beautiful reports.

**Tech Stack:**
- **Backend:** Python 3 + Flask
- **Database:** MySQL
- **Frontend:** Bootstrap 5 + Chart.js
- **Auth:** Flask-Login (session-based)

---

## Features

- User registration & login
- Add / Edit / Delete expenses
- Custom categories with icons & colors
- Monthly & category-wise budgets with progress tracking
- Smart insights (highest spending category, budget alerts, daily average, payment method analysis)
- Dashboard with pie chart & monthly trend
- Advanced filters on expenses (search, category, date range)
- Yearly reports with charts
- Fully responsive UI

---

## Project Structure

```
smart-expense-analyzer/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # Database models
│   ├── forms.py             # WTForms
│   ├── routes.py            # All routes & logic
│   ├── templates/           # Jinja2 templates
│   └── static/
│       ├── css/style.css
│       └── js/
├── config.py
├── run.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Prerequisites

- Python 3.10+
- MySQL 8.0+
- pip

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd smart-expense-analyzer
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create MySQL database

```sql
CREATE DATABASE expense_analyzer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'expense_user'@'localhost' IDENTIFIED BY 'expense_pass';
GRANT ALL PRIVILEGES ON expense_analyzer.* TO 'expense_user'@'localhost';
FLUSH PRIVILEGES;
```

> You can change the username/password. Just update `.env` accordingly.

### 5. Configure environment

```bash
cp .env.example .env
# Edit .env if needed
```

### 6. Run the application

```bash
python run.py
```

Open http://127.0.0.1:5000 in your browser.

---

## Default Database Credentials (as configured)

| Setting   | Value              |
|-----------|--------------------|
| Host      | localhost          |
| Database  | expense_analyzer   |
| User      | expense_user       |
| Password  | expense_pass       |

---

## How to Use

1. **Register** a new account (default categories are created automatically).
2. Go to **Dashboard** to see overview & insights.
3. **Add Expenses** from the Expenses page.
4. Set **Budgets** (overall or per category).
5. View **Reports** for yearly analysis.

---

## Screenshots Features

- Modern gradient landing page
- Clean dashboard with charts
- Responsive expense table with filters
- Budget progress bars with color coding
- Smart insights panel

---

## License

MIT License — feel free to use and modify.

---

Made with ❤️ for better financial control.


## Learn Full Stack Development

Want to build projects like this?

- [Full Stack Development Training Course in Noida](https://uncodemy.com/course/full-stack-development-training-course-in-noida)
- [Full Stack Development Training Course in Delhi](https://uncodemy.com/course/full-stack-development-training-course-in-delhi)
