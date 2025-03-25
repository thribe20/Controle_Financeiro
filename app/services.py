import os
from ofxparse import OfxParser
from app import db
from app.models import Transaction, Category, CategoryKeyword


def import_ofx(file_path):
    """Importa transações de um arquivo OFX"""
    transactions = []
    print(f"Iniciando importação do arquivo: {file_path}")

    with open(file_path, 'rb') as file:
        ofx = OfxParser.parse(file)

    account = ofx.account

    for ofx_transaction in account.statement.transactions:
        # Verificar se a transação já existe
        existing = Transaction.query.filter_by(external_id=ofx_transaction.id).first()

        if not existing:
            # Criar nova transação
            transaction = Transaction(
                external_id=ofx_transaction.id,
                date=ofx_transaction.date,
                amount=float(ofx_transaction.amount),
                description=ofx_transaction.memo or ofx_transaction.payee,
                source_filename=os.path.basename(file_path)
            )

            transactions.append(transaction)

    return transactions


def categorize_transaction(transaction):
    """Categoriza automaticamente uma transação baseada nas palavras-chave"""
    print(f"Tentando categorizar: {transaction.description}")

    if transaction.category_id:
        print(f"Já categorizada como: {transaction.category_id}")
        return False  # Já está categorizada

    # Para receitas, buscar apenas em categorias de receita
    is_expense = transaction.amount < 0
    print(f"É despesa: {is_expense}")

    # Obter todas as categorias com suas palavras-chave
    categories = Category.query.filter_by(is_expense=is_expense).all()
    print(f"Categorias encontradas: {len(categories)}")

    # Se não houver categorias do tipo correto, não faz nada
    if not categories:
        print("Nenhuma categoria encontrada do tipo correto")
        return False

    for category in categories:
        print(f"Verificando categoria: {category.name}")
        # Obter palavras-chave da categoria
        keywords = CategoryKeyword.query.filter_by(category_id=category.id).all()
        print(f"Palavras-chave encontradas: {len(keywords)}")

        # Se não tem palavras-chave, continua para a próxima categoria
        if not keywords:
            continue

        # Verificar se alguma palavra-chave está na descrição
        description = transaction.description.lower()
        for keyword in keywords:
            print(f"Verificando palavra-chave: '{keyword.keyword}' (tipo: {keyword.match_type})")
            if keyword.match_type == 'exact':
                print(f"Comparando exato: '{keyword.keyword.lower()}' == '{description}'")
                # Comparação exata (ignorando maiúsculas/minúsculas)
                if keyword.keyword.lower() == description:
                    print(f"Match exato encontrado! Categoria: {category.name}")
                    transaction.category_id = category.id
                    return True
            else:  # 'contains' é o padrão
                print(f"Procurando: '{keyword.keyword.lower()}' em '{description}'")
                # Verificar se contém a palavra-chave
                if keyword.keyword.lower() in description:
                    print(f"Match contém encontrado! Categoria: {category.name}")
                    transaction.category_id = category.id
                    return True

    print("Nenhuma correspondência encontrada.")
    return False


def criar_categorias_padrao():
    """Cria categorias básicas para despesas e receitas"""
    categorias = [
        # Despesas
        {"nome": "Alimentação", "cor": "#FF5733", "despesa": True},
        {"nome": "Moradia", "cor": "#C70039", "despesa": True},
        {"nome": "Transporte", "cor": "#900C3F", "despesa": True},
        {"nome": "Saúde", "cor": "#581845", "despesa": True},
        {"nome": "Educação", "cor": "#FFC300", "despesa": True},
        {"nome": "Lazer", "cor": "#DAF7A6", "despesa": True},
        {"nome": "Vestuário", "cor": "#9B59B6", "despesa": True},
        {"nome": "Cartão de Crédito", "cor": "#3498DB", "despesa": True},
        {"nome": "Serviços", "cor": "#2ECC71", "despesa": True},
        {"nome": "Impostos", "cor": "#7D3C98", "despesa": True},

        # Receitas
        {"nome": "Salário", "cor": "#27AE60", "despesa": False},
        {"nome": "Investimentos", "cor": "#2E86C1", "despesa": False},
        {"nome": "Transferências", "cor": "#F39C12", "despesa": False},
    ]

    # Criar as categorias básicas
    for cat_info in categorias:
        # Verifica se a categoria já existe
        categoria = Category.query.filter_by(name=cat_info["nome"]).first()

        # Se não existir, cria a categoria
        if not categoria:
            categoria = Category(
                name=cat_info["nome"],
                description=cat_info["nome"],
                color=cat_info["cor"],
                is_expense=cat_info["despesa"]
            )
            db.session.add(categoria)

    db.session.commit()
    print("Categorias básicas criadas com sucesso!")