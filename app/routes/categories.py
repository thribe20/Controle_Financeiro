from flask import Blueprint, render_template, redirect, url_for, request, flash
from app import db
from app.models import Category, CategoryKeyword
from app.forms import CategoryForm, KeywordForm

category_bp = Blueprint('categories', __name__, url_prefix='/categories')


@category_bp.route('/')
def index():
    """Lista todas as categorias"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('categories/list.html', title='Categorias', categories=categories)


@category_bp.route('/create', methods=['GET', 'POST'])
def create_category():
    """Cria uma nova categoria"""
    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data,
            color=form.color.data,
            is_expense=form.is_expense.data
        )

        db.session.add(category)
        db.session.commit()

        flash('Categoria criada com sucesso!', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/form.html', form=form, title='Nova Categoria')


@category_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_category(id):
    """Edita uma categoria existente"""
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()

        flash('Categoria atualizada com sucesso!', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/form.html', form=form, category=category, title='Editar Categoria')


@category_bp.route('/<int:id>/delete', methods=['POST'])
def delete_category(id):
    """Exclui uma categoria"""
    category = Category.query.get_or_404(id)

    db.session.delete(category)
    db.session.commit()

    flash('Categoria excluída com sucesso!', 'success')
    return redirect(url_for('categories.index'))


@category_bp.route('/<int:id>/keywords', methods=['GET', 'POST'])
def manage_keywords(id):
    """Gerencia palavras-chave de uma categoria"""
    category = Category.query.get_or_404(id)
    form = KeywordForm()

    if form.validate_on_submit():
        keyword = CategoryKeyword(
            keyword=form.keyword.data,
            match_type=form.match_type.data,
            category_id=category.id
        )

        db.session.add(keyword)
        db.session.commit()

        flash('Palavra-chave adicionada com sucesso!', 'success')
        return redirect(url_for('categories.manage_keywords', id=category.id))

    keywords = CategoryKeyword.query.filter_by(category_id=category.id).all()

    return render_template('categories/keywords.html',
                           category=category,
                           form=form,
                           keywords=keywords)


@category_bp.route('/keywords/<int:id>/delete', methods=['POST'])
def delete_keyword(id):
    """Exclui uma palavra-chave"""
    keyword = CategoryKeyword.query.get_or_404(id)
    category_id = keyword.category_id

    db.session.delete(keyword)
    db.session.commit()

    flash('Palavra-chave excluída com sucesso!', 'success')
    return redirect(url_for('categories.manage_keywords', id=category_id))