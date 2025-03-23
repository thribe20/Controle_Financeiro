from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService
from app.services.report_service import ReportService

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@login_required
def index():
    """Página principal do dashboard"""
    # Obter serviços
    tx_service = TransactionService(current_user)
    cat_service = CategoryService(current_user)

    # Obter estatísticas das categorias
    cat_stats = cat_service.get_stats()

    # Obter ano atual para os gráficos
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Obter resumo mensal para o ano atual
    monthly_summary = tx_service.get_monthly_summary(current_year)

    # Calcular receitas e despesas do mês atual
    current_month_data = [s for s in monthly_summary if s.month == current_month]

    income = 0
    expenses = 0

    for item in current_month_data:
        if item.total_amount > 0:
            income += item.total_amount
        else:
            expenses += abs(item.total_amount)

    balance = income - expenses

    # Variáveis para o template
    context = {
        'total_transactions': cat_stats['total_transactions'],
        'categorized_transactions': cat_stats['categorized_transactions'],
        'categorization_rate': cat_stats['categorization_rate'],
        'income': income,
        'expenses': expenses,
        'balance': balance,
        'current_month': current_month,
        'current_year': current_year
    }

    return render_template('dashboard/index.html', **context)


@bp.route('/charts/<chart_type>')
@login_required
def get_chart(chart_type):
    """Endpoint para obter gráficos para o dashboard"""
    report_service = ReportService(current_user)

    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not year:
        year = datetime.now().year

    if chart_type == 'expenses':
        # Gráfico de despesas por categoria
        image_bytes = report_service.plot_monthly_expenses(year)
        return jsonify({'image_data': image_bytes})

    elif chart_type == 'category_breakdown':
        # Gráfico de distribuição por categoria
        image_bytes = report_service.plot_category_breakdown(year, month)
        return jsonify({'image_data': image_bytes})

    elif chart_type == 'income_vs_expenses':
        # Gráfico de receitas vs despesas
        image_bytes = report_service.plot_income_vs_expenses(year)
        return jsonify({'image_data': image_bytes})

    else:
        return jsonify({'error': 'Tipo de gráfico inválido'}), 400


@bp.route('/stats')
@login_required
def get_stats():
    """Endpoint para obter estatísticas para o dashboard"""
    # Obter serviços
    tx_service = TransactionService(current_user)

    # Obter parâmetros
    year = request.args.get('year', type=int, default=datetime.now().year)

    # Obter resumo mensal
    monthly_summary = tx_service.get_monthly_summary(year)

    # Processar dados para formato adequado para gráficos
    months = list(range(1, 13))
    income_data = [0] * 12
    expense_data = [0] * 12

    for item in monthly_summary:
        if item.month in months:
            idx = item.month - 1  # Ajustar para índice 0-11
            if item.total_amount > 0:
                income_data[idx] = float(item.total_amount)
            else:
                expense_data[idx] = float(abs(item.total_amount))

    # Formatação para labels do gráfico
    month_labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                    'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

    return jsonify({
        'labels': month_labels,
        'income': income_data,
        'expenses': expense_data
    })