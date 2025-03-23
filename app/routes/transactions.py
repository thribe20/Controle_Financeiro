from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.transaction_service import TransactionService
from app.services.category_service import CategoryService
from app.services.ofx_parser import OFXImportService
from app.forms.transaction_forms import TransactionFilterForm, TransactionEditForm, UploadForm
from sqlalchemy import extract
from datetime import datetime

bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@bp.route('/')
@login_required
def index():
    """Lista de transações com filtros"""
    # Configuração do formulário de filtro
    form = TransactionFilterForm()

    # Preencher opções de categorias
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    form.category.choices = [(0, 'Todas as Categorias')] + [(c.id, c.name) for c in categories]

    # Obter parâmetros de filtro da URL
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    category_id = request.args.get('category', type=int)

    # Configurar valores padrão
    if not year:
        year = datetime.now().year

    # Aplicar valores aos campos do formulário
    form.year.data = year
    if month:
        form.month.data = month
    if category_id:
        form.category.data = category_id

    # Obter transações filtradas
    tx_service = TransactionService(current_user)
    transactions = tx_service.get_by_period(year, month, category_id if category_id and category_id > 0 else None)

    return render_template(
        'transactions/index.html',
        title='Transações',
        form=form,
        transactions=transactions,
        year=year,
        month=month
    )


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Importação de arquivo OFX"""
    form = UploadForm()

    if form.validate_on_submit():
        try:
            # Importar arquivo
            ofx_service = OFXImportService(current_user)
            transactions_count = ofx_service.import_transactions(form.file.data)

            flash(f'Arquivo importado com sucesso! {transactions_count} novas transações adicionadas.', 'success')
            return redirect(url_for('transactions.index'))
        except ValueError as e:
            flash(f'Erro ao importar arquivo: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Erro inesperado ao processar o arquivo: {str(e)}', 'danger')

    return render_template('transactions/upload.html', title='Importar OFX', form=form)


@bp.route('/edit/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit(transaction_id):
    """Edição de transação"""
    # Buscar a transação
    tx_service = TransactionService(current_user)
    transaction = tx_service.get_by_id(transaction_id)

    if not transaction:
        flash('Transação não encontrada.', 'danger')
        return redirect(url_for('transactions.index'))

    # Configurar formulário
    form = TransactionEditForm()

    # Preencher opções de categorias
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name).all()
    form.category_id.choices = [(0, 'Sem Categoria')] + [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        # Atualizar categoria
        category_id = form.category_id.data if form.category_id.data > 0 else None
        tx_service.update_category(transaction_id, category_id)

        # Atualizar observações
        tx_service.update_notes(transaction_id, form.notes.data)

        # Atualizar status de reconciliação
        tx_service.reconcile(transaction_id, form.is_reconciled.data)

        flash('Transação atualizada com sucesso!', 'success')
        return redirect(url_for('transactions.index', year=transaction.year, month=transaction.month))
    elif request.method == 'GET':
        # Preencher formulário com dados da transação
        form.category_id.data = transaction.category_id if transaction.category_id else 0
        form.notes.data = transaction.notes
        form.is_reconciled.data = transaction.is_reconciled

    return render_template(
        'transactions/edit.html',
        title='Editar Transação',
        form=form,
        transaction=transaction
    )


@bp.route('/recategorize')
@login_required
def recategorize_all():
    """Recategoriza todas as transações"""
    tx_service = TransactionService(current_user)
    count = tx_service.auto_categorize_all(recategorize_all=True)

    flash(f'{count} transações foram recategorizadas com sucesso!', 'success')
    return redirect(url_for('transactions.index'))


@bp.route('/api/list')
@login_required
def api_list():
    """API endpoint para listar transações (usado para AJAX)"""
    # Obter parâmetros
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    category_id = request.args.get('category_id', type=int)

    # Configurar valores padrão
    if not year:
        year = datetime.now().year

    # Obter transações filtradas
    tx_service = TransactionService(current_user)
    transactions = tx_service.get_by_period(year, month, category_id if category_id and category_id > 0 else None)

    # Converter para lista de dicionários
    result = []
    for tx in transactions:
        category_name = tx.category.name if tx.category else 'Sem Categoria'
        result.append({
            'id': tx.id,
            'date': tx.date.strftime('%d/%m/%Y'),
            'description': tx.description,
            'amount': float(tx.amount),
            'category': category_name,
            'is_reconciled': tx.is_reconciled
        })

    return jsonify({'transactions': result})


@bp.route('/api/update-category', methods=['POST'])
@login_required
def api_update_category():
    """API endpoint para atualizar categoria (usado para AJAX)"""
    # Obter dados do JSON
    data = request.get_json()

    if not data or 'transaction_id' not in data or 'category_id' not in data:
        return jsonify({'success': False, 'message': 'Dados inválidos'}), 400

    transaction_id = data['transaction_id']
    category_id = data['category_id'] if data['category_id'] > 0 else None

    # Atualizar categoria
    tx_service = TransactionService(current_user)
    success = tx_service.update_category(transaction_id, category_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Falha ao atualizar categoria'}), 400