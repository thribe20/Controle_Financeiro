from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from app import db
from app.models import Transaction, Category, CategoryKeyword
from app.forms import UploadForm
from app.services import import_ofx, categorize_transaction

transaction_bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@transaction_bp.route('/')
@transaction_bp.route('/')
def list_transactions():
    """Lista todas as transações com filtros"""
    # Obter parâmetros de filtro
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    category_id = request.args.get('category_id', type=int)

    # Construir query
    query = Transaction.query

    # Aplicar filtros
    if year is not None:
        query = query.filter(Transaction.year == year)

    if month is not None:
        query = query.filter(Transaction.month == month)

    if category_id is not None:
        if category_id == -1:  # Sem categoria
            query = query.filter(Transaction.category_id == None)
        else:
            query = query.filter(Transaction.category_id == category_id)

    # Executar query
    transactions = query.order_by(Transaction.date.desc()).all()

    # Adicione print para debug
    print(f"Filtros aplicados: ano={year}, mês={month}, categoria={category_id}")
    print(f"Total de transações após filtros: {len(transactions)}")

    # Obter todas as categorias para o formulário de filtro
    categories = Category.query.order_by(Category.name).all()

    # Obter anos e meses únicos para o filtro
    years = db.session.query(Transaction.year).distinct().order_by(Transaction.year.desc()).all()
    years = [y[0] for y in years]

    # Se não houver anos nos dados, use o ano atual
    if not years:
        years = [datetime.now().year]

    return render_template('transactions/list.html',
                           transactions=transactions,
                           categories=categories,
                           years=years,
                           selected_year=year,
                           selected_month=month,
                           selected_category=category_id)


@transaction_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    # código existente
    pass


@transaction_bp.route('/<int:id>/category', methods=['POST'])
def update_category(id):
    # código existente
    pass


# Adicione a nova rota de recategorização como uma função separada no nível principal
@transaction_bp.route('/recategorize')
def recategorize_all():
    """Recategoriza todas as transações sem categoria"""
    transactions = Transaction.query.filter_by(category_id=None).all()
    print(f"Encontradas {len(transactions)} transações sem categoria")

    count = 0
    for transaction in transactions:
        print(f"\n--- Transação: {transaction.description} ---")
        # Verificar categorias disponíveis
        is_expense = transaction.amount < 0
        categories = Category.query.filter_by(is_expense=is_expense).all()
        print(f"Categorias disponíveis ({len(categories)}):")
        for cat in categories:
            keywords = CategoryKeyword.query.filter_by(category_id=cat.id).all()
            print(f"  - {cat.name} ({len(keywords)} palavras-chave)")
            for kw in keywords:
                print(f"    * '{kw.keyword}' ({kw.match_type})")

                # Testar manualmente cada palavra-chave
                if kw.match_type == 'exact':
                    if kw.keyword.lower() == transaction.description.lower():
                        print(f"    >>> MATCH EXACT ENCONTRADO!")
                else:  # 'contains'
                    if kw.keyword.lower() in transaction.description.lower():
                        print(f"    >>> MATCH CONTAINS ENCONTRADO!")

        # Agora tente categorizar
        success = categorize_transaction(transaction)
        if success:
            count += 1
            print(f">>> Transação categorizada com sucesso: {transaction.category.name}")
        else:
            print(">>> Transação não foi categorizada")

    # Salvar alterações
    db.session.commit()

    flash(f'{count} transações foram categorizadas automaticamente.', 'success')
    return redirect(url_for('transactions.list_transactions'))


# Adicione aqui as outras rotas de diagnóstico
@transaction_bp.route('/debug_keywords')
def debug_keywords():
    """Depura palavras-chave e seus tipos de correspondência"""
    # Busca todas as palavras-chave
    keywords = CategoryKeyword.query.all()
    output = []

    for keyword in keywords:
        # Tenta acessar o atributo match_type
        try:
            match_type = keyword.match_type
            category = Category.query.get(keyword.category_id)
            category_name = category.name if category else "Desconhecida"
            output.append(f"Palavra-chave: '{keyword.keyword}', Tipo: '{match_type}', Categoria: {category_name}")
        except Exception as e:
            output.append(f"Erro ao acessar match_type: {str(e)}")

    if not output:
        output.append("Nenhuma palavra-chave encontrada.")

    # Retorna como texto simples
    return "<br>".join(output)


@transaction_bp.route('/test_match/<int:transaction_id>/<int:keyword_id>')
def test_match(transaction_id, keyword_id):
    """Testa especificamente uma palavra-chave em uma transação"""
    transaction = Transaction.query.get_or_404(transaction_id)
    keyword = CategoryKeyword.query.get_or_404(keyword_id)

    output = []
    output.append(f"Transação: {transaction.description}")
    output.append(f"Palavra-chave: {keyword.keyword}")

    try:
        match_type = keyword.match_type
        output.append(f"Tipo de correspondência: {match_type}")
    except Exception as e:
        output.append(f"Erro ao acessar match_type: {str(e)}")
        return "<br>".join(output)

    # Teste de 'contém'
    transaction_lower = transaction.description.lower()
    keyword_lower = keyword.keyword.lower()

    output.append(f"Transação (lower): '{transaction_lower}'")
    output.append(f"Palavra-chave (lower): '{keyword_lower}'")

    if keyword_lower in transaction_lower:
        output.append("<b style='color:green'>MATCH ENCONTRADO!</b>")
        # Tenta categorizar
        transaction.category_id = keyword.category_id
        db.session.commit()
        output.append(f"Transação categorizada como {keyword.category.name}")
    else:
        output.append("<b style='color:red'>NÃO HÁ CORRESPONDÊNCIA</b>")
        # Tenta visualizar caracteres exatos
        output.append("Códigos ASCII da transação:")
        output.append(" ".join(str(ord(c)) for c in transaction.description))
        output.append("Códigos ASCII da palavra-chave:")
        output.append(" ".join(str(ord(c)) for c in keyword.keyword))

    return "<br>".join(output)