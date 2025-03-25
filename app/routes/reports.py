from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import calendar
from app import db
from app.models import Transaction, Category

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
def index():
    """Página principal de relatórios"""
    # Obter anos disponíveis para o filtro
    years = db.session.query(Transaction.year).distinct().order_by(Transaction.year.desc()).all()
    years = [y[0] for y in years]

    # Se não houver anos nos dados, use o ano atual
    if not years:
        years = [datetime.now().year]

    # Usar o ano atual como padrão, ou o mais recente disponível
    current_year = datetime.now().year
    selected_year = request.args.get('year', type=int, default=current_year if current_year in years else years[0])

    return render_template('reports/index.html',
                           years=years,
                           selected_year=selected_year)


@reports_bp.route('/data/category_spending')
def category_spending():
    """Retorna dados de gastos por categoria para o ano selecionado"""
    year = request.args.get('year', type=int, default=datetime.now().year)

    # Consulta para obter gastos por categoria (apenas despesas - valores negativos)
    category_data = db.session.query(
        Category.name,
        Category.color,
        func.sum(Transaction.amount).label('total')
    ).join(
        Transaction,
        Transaction.category_id == Category.id
    ).filter(
        Transaction.year == year,
        Transaction.amount < 0  # Apenas despesas
    ).group_by(
        Category.id
    ).order_by(
        func.sum(Transaction.amount)
    ).all()

    # Transformar em lista para JSON
    result = []
    for name, color, total in category_data:
        result.append({
            'name': name,
            'color': color,
            'value': abs(float(total))  # Converter para positivo para o gráfico
        })

    # Adicionar categoria "Sem categoria" se houver gastos não categorizados
    uncategorized = db.session.query(
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.year == year,
        Transaction.amount < 0,  # Apenas despesas
        Transaction.category_id == None
    ).scalar() or 0

    if uncategorized < 0:  # Se houver gastos não categorizados
        result.append({
            'name': 'Sem categoria',
            'color': '#CCCCCC',
            'value': abs(float(uncategorized))
        })

    return jsonify(result)


@reports_bp.route('/data/monthly_spending')
def monthly_spending():
    """Retorna dados de gastos mensais para o ano selecionado"""
    year = request.args.get('year', type=int, default=datetime.now().year)

    # Inicializar array com todos os meses
    monthly_data = []
    for month in range(1, 13):
        monthly_data.append({
            'month': month,
            'month_name': calendar.month_name[month],
            'expenses': 0,
            'income': 0
        })

    # Consulta para obter gastos mensais
    monthly_expenses = db.session.query(
        Transaction.month,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.year == year,
        Transaction.amount < 0  # Apenas despesas
    ).group_by(
        Transaction.month
    ).all()

    # Preencher dados de despesas
    for month, total in monthly_expenses:
        if 1 <= month <= 12:  # Verificar se o mês está no intervalo válido
            monthly_data[month - 1]['expenses'] = abs(float(total))  # Converter para positivo

    # Consulta para obter receitas mensais
    monthly_income = db.session.query(
        Transaction.month,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.year == year,
        Transaction.amount > 0  # Apenas receitas
    ).group_by(
        Transaction.month
    ).all()

    # Preencher dados de receitas
    for month, total in monthly_income:
        if 1 <= month <= 12:  # Verificar se o mês está no intervalo válido
            monthly_data[month - 1]['income'] = float(total)

    return jsonify(monthly_data)


@reports_bp.route('/data/kpi_summary')
def kpi_summary():
    """Retorna resumo dos principais indicadores financeiros"""
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int)  # Opcional

    # Base de filtros
    filters = [Transaction.year == year]

    # Se o mês for especificado, adicionar ao filtro
    if month:
        filters.append(Transaction.month == month)
        period_name = f"{calendar.month_name[month]} {year}"
    else:
        period_name = f"{year}"

    # Total de despesas
    expenses = db.session.query(func.sum(Transaction.amount)).filter(
        *filters, Transaction.amount < 0
    ).scalar() or 0

    # Total de receitas
    income = db.session.query(func.sum(Transaction.amount)).filter(
        *filters, Transaction.amount > 0
    ).scalar() or 0

    # Saldo
    balance = income + expenses  # expenses já é negativo

    # Mês anterior para comparação
    if month:
        # Se mês atual é janeiro, mês anterior é dezembro do ano anterior
        prev_month = 12 if month == 1 else month - 1
        prev_year = year - 1 if month == 1 else year

        prev_filters = [Transaction.year == prev_year, Transaction.month == prev_month]

        prev_expenses = db.session.query(func.sum(Transaction.amount)).filter(
            *prev_filters, Transaction.amount < 0
        ).scalar() or 0

        prev_income = db.session.query(func.sum(Transaction.amount)).filter(
            *prev_filters, Transaction.amount > 0
        ).scalar() or 0

        # Calcular variações percentuais
        if prev_expenses != 0:
            expense_change = ((abs(expenses) - abs(prev_expenses)) / abs(prev_expenses)) * 100
        else:
            expense_change = 0

        if prev_income != 0:
            income_change = ((income - prev_income) / prev_income) * 100
        else:
            income_change = 0
    else:
        # Comparar com ano anterior
        prev_filters = [Transaction.year == year - 1]

        prev_expenses = db.session.query(func.sum(Transaction.amount)).filter(
            *prev_filters, Transaction.amount < 0
        ).scalar() or 0

        prev_income = db.session.query(func.sum(Transaction.amount)).filter(
            *prev_filters, Transaction.amount > 0
        ).scalar() or 0

        # Calcular variações percentuais
        if prev_expenses != 0:
            expense_change = ((abs(expenses) - abs(prev_expenses)) / abs(prev_expenses)) * 100
        else:
            expense_change = 0

        if prev_income != 0:
            income_change = ((income - prev_income) / prev_income) * 100
        else:
            income_change = 0

    # Top categorias de despesa
    top_categories = db.session.query(
        Category.name,
        func.sum(Transaction.amount).label('total')
    ).join(
        Transaction,
        Transaction.category_id == Category.id
    ).filter(
        *filters,
        Transaction.amount < 0  # Apenas despesas
    ).group_by(
        Category.id
    ).order_by(
        func.sum(Transaction.amount)
    ).limit(5).all()

    top_categories_data = [
        {'name': name, 'total': abs(float(total))}
        for name, total in top_categories
    ]

    return jsonify({
        'period': period_name,
        'expenses': abs(float(expenses)),
        'income': float(income),
        'balance': float(balance),
        'expense_change': float(expense_change),
        'income_change': float(income_change),
        'top_categories': top_categories_data
    })