from flask import Blueprint, render_template, redirect, url_for, flash  # Adicione "flash" aqui
from datetime import datetime
from app import db
from app.models import Transaction, Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    # Obter último mês com transações
    latest = Transaction.query.order_by(Transaction.date.desc()).first()
    year = latest.year if latest else datetime.now().year
    month = latest.month if latest else datetime.now().month

    # Buscar dados para dashboard
    income = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.year == year,
        Transaction.month == month,
        Transaction.amount > 0
    ).scalar() or 0

    expenses = db.session.query(db.func.sum(Transaction.amount)).filter(
        Transaction.year == year,
        Transaction.month == month,
        Transaction.amount < 0
    ).scalar() or 0

    expenses = abs(expenses)  # Transformar em valor positivo para exibição
    balance = income - expenses

    # Dados para gráfico de categorias
    category_data = db.session.query(
        Category.name,
        Category.color,
        db.func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.year == year,
        Transaction.month == month,
        Transaction.amount < 0  # Apenas despesas para o gráfico
    ).group_by(Category.id).all()

    return render_template('index.html',
                           year=year,
                           month=month,
                           income=income,
                           expenses=expenses,
                           balance=balance,
                           category_data=category_data)


# Adicione esta rota ao seu arquivo app/routes/main.py

@main_bp.route('/initialize')
def initialize():
    """Inicializa as categorias padrão do sistema"""
    from app.services import criar_categorias_padrao

    criar_categorias_padrao()

    flash('Sistema inicializado com categorias padrão', 'success')
    return redirect(url_for('main.index'))