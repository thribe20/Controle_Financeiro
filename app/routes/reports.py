from flask import Blueprint, render_template, request, send_file, make_response, flash, redirect, url_for
from flask_login import login_required, current_user
from io import BytesIO
from datetime import datetime
import os
from app.services.report_service import ReportService
from app.forms.report_forms import ReportFilterForm

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.route('/')
@login_required
def index():
    """Página principal de relatórios"""
    form = ReportFilterForm()

    # Obter ano atual para valores padrão
    current_year = datetime.now().year

    # Preencher anos disponíveis
    from app.models.transaction import Transaction
    years = Transaction.query.with_entities(Transaction.year).filter_by(
        user_id=current_user.id
    ).distinct().order_by(Transaction.year.desc()).all()

    form.year.choices = [(y[0], str(y[0])) for y in years] if years else [(current_year, str(current_year))]

    # Obter parâmetros da URL
    year = request.args.get('year', type=int)
    if not year and years:
        year = years[0][0]
    elif not year:
        year = current_year

    # Aplicar aos campos do formulário
    form.year.data = year

    return render_template(
        'reports/index.html',
        title='Relatórios',
        form=form,
        year=year
    )


@bp.route('/monthly-expenses')
@login_required
def monthly_expenses():
    """Relatório de despesas mensais"""
    # Obter parâmetros
    year = request.args.get('year', type=int, default=datetime.now().year)

    # Gerar o gráfico
    report_service = ReportService(current_user)
    image_data = report_service.plot_monthly_expenses(year)

    # Retornar a imagem como resposta
    response = make_response(image_data)
    response.headers.set('Content-Type', 'image/png')
    return response


@bp.route('/category-breakdown')
@login_required
def category_breakdown():
    """Relatório de distribuição por categoria"""
    # Obter parâmetros
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int)

    # Gerar o gráfico
    report_service = ReportService(current_user)
    image_data = report_service.plot_category_breakdown(year, month)

    # Retornar a imagem como resposta
    response = make_response(image_data)
    response.headers.set('Content-Type', 'image/png')
    return response


@bp.route('/income-vs-expenses')
@login_required
def income_vs_expenses():
    """Relatório de receitas vs despesas"""
    # Obter parâmetros
    year = request.args.get('year', type=int, default=datetime.now().year)

    # Gerar o gráfico
    report_service = ReportService(current_user)
    image_data = report_service.plot_income_vs_expenses(year)

    # Retornar a imagem como resposta
    response = make_response(image_data)
    response.headers.set('Content-Type', 'image/png')
    return response


@bp.route('/summary')
@login_required
def summary():
    """Resumo financeiro com tabelas"""
    # Obter parâmetros
    year = request.args.get('year', type=int, default=datetime.now().year)

    # Gerar resumo mensal
    report_service = ReportService(current_user)
    monthly_df = report_service.generate_monthly_summary(year, as_dataframe=True)

    # Gerar resumo por categoria
    category_df = report_service.generate_category_summary(year, as_dataframe=True)

    # Verificar se há dados
    if monthly_df.empty:
        flash('Não há dados para o período selecionado.', 'warning')
        return redirect(url_for('reports.index'))

    # Converter DataFrames para HTML para exibição
    monthly_table = monthly_df.to_html(classes='table table-striped', index=False)
    category_table = category_df.to_html(classes='table table-striped', index=False) if not category_df.empty else None

    return render_template(
        'reports/summary.html',
        title=f'Resumo Financeiro - {year}',
        monthly_table=monthly_table,
        category_table=category_table,
        year=year
    )


@bp.route('/export-csv')
@login_required
def export_csv():
    """Exportar transações para CSV"""
    from app.services.transaction_service import TransactionService
    import csv

    # Obter parâmetros
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    # Obter transações
    tx_service = TransactionService(current_user)
    transactions = tx_service.get_by_period(year, month)

    if not transactions:
        flash('Não há transações para o período selecionado.', 'warning')
        return redirect(url_for('reports.index'))

    # Criar CSV na memória
    output = BytesIO()
    writer = csv.writer(output)

    # Escrever cabeçalho
    writer.writerow(['Data', 'Descrição', 'Valor', 'Categoria', 'Observações'])

    # Escrever transações
    for tx in transactions:
        writer.writerow([
            tx.date.strftime('%d/%m/%Y'),
            tx.description,
            tx.amount,
            tx.category.name if tx.category else 'Sem Categoria',
            tx.notes or ''
        ])

    # Preparar resposta
    output.seek(0)

    # Nome do arquivo
    filename = f"transacoes_{year}"
    if month:
        filename += f"_{month}"
    filename += ".csv"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )