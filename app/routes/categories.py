from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.category import Category, CategoryKeyword
from app.services.category_service import CategoryService
from app.forms.category_forms import CategoryForm, CategoryKeywordForm

bp = Blueprint('categories', __name__, url_prefix='/categories')


@bp.route('/')
@login_required
def index():
    """Lista de categorias"""
    cat_service = CategoryService(current_user)
    categories = cat_service.get_all()

    return render_template(
        'categories/index.html',
        title='Categorias',
        categories=categories
    )


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Criar nova categoria"""
    form = CategoryForm()

    if form.validate_on_submit():
        cat_service = CategoryService(current_user)

        category = cat_service.create(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            is_expense=form.is_expense.data
        )

        if category:
            flash('Categoria criada com sucesso!', 'success')
            return redirect(url_for('categories.index'))
        else:
            flash('Erro ao criar categoria. O nome pode já estar em uso.', 'danger')

    return render_template(
        'categories/form.html',
        title='Nova Categoria',
        form=form,
        is_edit=False
    )


@bp.route('/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit(category_id):
    """Editar categoria existente"""
    cat_service = CategoryService(current_user)
    category = cat_service.get_by_id(category_id)

    if not category:
        flash('Categoria não encontrada.', 'danger')
        return redirect(url_for('categories.index'))

    form = CategoryForm()

    if form.validate_on_submit():
        success = cat_service.update(
            category_id=category_id,
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            is_expense=form.is_expense.data
        )

        if success:
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('categories.view', category_id=category_id))
        else:
            flash('Erro ao atualizar categoria. O nome pode já estar em uso.', 'danger')
    elif request.method == 'GET':
        # Preencher o formulário com os dados da categoria
        form.name.data = category.name
        form.description.data = category.description
        form.color.data = category.color
        form.is_expense.data = category.is_expense

    return render_template(
        'categories/form.html',
        title='Editar Categoria',
        form=form,
        category=category,
        is_edit=True
    )


@bp.route('/view/<int:category_id>')
@login_required
def view(category_id):
    """Visualizar detalhes de uma categoria"""
    cat_service = CategoryService(current_user)
    category = cat_service.get_by_id(category_id)

    if not category:
        flash('Categoria não encontrada.', 'danger')
        return redirect(url_for('categories.index'))

    # Formulário para adicionar palavras-chave
    keyword_form = CategoryKeywordForm()

    # Obter transações desta categoria
    from app.services.transaction_service import TransactionService
    tx_service = TransactionService(current_user)
    transactions = Transaction.query.filter_by(
        user_id=current_user.id,
        category_id=category_id
    ).order_by(Transaction.date.desc()).limit(10).all()

    return render_template(
        'categories/view.html',
        title=f'Categoria: {category.name}',
        category=category,
        transactions=transactions,
        keyword_form=keyword_form
    )


@bp.route('/delete/<int:category_id>', methods=['POST'])
@login_required
def delete(category_id):
    """Excluir categoria"""
    cat_service = CategoryService(current_user)

    success = cat_service.delete(category_id)

    if success:
        flash('Categoria excluída com sucesso!', 'success')
    else:
        flash('Erro ao excluir categoria.', 'danger')

    return redirect(url_for('categories.index'))


@bp.route('/<int:category_id>/keywords', methods=['GET', 'POST'])
@login_required
def manage_keywords(category_id):
    """Gerenciar palavras-chave de uma categoria"""
    cat_service = CategoryService(current_user)
    category = cat_service.get_by_id(category_id)

    if not category:
        flash('Categoria não encontrada.', 'danger')
        return redirect(url_for('categories.index'))

    form = CategoryKeywordForm()

    if form.validate_on_submit():
        success = cat_service.add_keyword(category_id, form.keyword.data)

        if success:
            flash('Palavra-chave adicionada com sucesso!', 'success')
        else:
            flash('Erro ao adicionar palavra-chave. Ela pode já existir nesta categoria.', 'danger')

        return redirect(url_for('categories.manage_keywords', category_id=category_id))

    return render_template(
        'categories/keywords.html',
        title=f'Palavras-chave: {category.name}',
        category=category,
        form=form
    )


@bp.route('/keywords/delete/<int:keyword_id>', methods=['POST'])
@login_required
def delete_keyword(keyword_id):
    """Excluir palavra-chave"""
    cat_service = CategoryService(current_user)

    # Obter a categoria para redirecionar depois
    keyword = CategoryKeyword.query.filter_by(id=keyword_id).first()

    if not keyword or keyword.category.user_id != current_user.id:
        flash('Palavra-chave não encontrada.', 'danger')
        return redirect(url_for('categories.index'))

    category_id = keyword.category_id

    success = cat_service.remove_keyword(keyword_id)

    if success:
        flash('Palavra-chave removida com sucesso!', 'success')
    else:
        flash('Erro ao remover palavra-chave.', 'danger')

    return redirect(url_for('categories.manage_keywords', category_id=category_id))


@bp.route('/api/list')
@login_required
def api_list():
    """API endpoint para listar categorias (usado para AJAX)"""
    cat_service = CategoryService(current_user)
    categories = cat_service.get_all()

    # Converter para lista de dicionários
    result = []
    for cat in categories:
        result.append({
            'id': cat.id,
            'name': cat.name,
            'color': cat.color,
            'is_expense': cat.is_expense
        })

    return jsonify({'categories': result})