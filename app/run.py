import os
from app import create_app, db
from app.models.user import User
from app.models.category import Category, CategoryKeyword
from app.models.transaction import Transaction
from app.models.uploaded_file import UploadedFile
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação
app = create_app()


# Definir contexto shell para Flask CLI
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'CategoryKeyword': CategoryKeyword,
        'Transaction': Transaction,
        'UploadedFile': UploadedFile
    }


# Adicionar comandos personalizados
@app.cli.command("create-db")
def create_db():
    """Cria as tabelas do banco de dados."""
    db.create_all()
    print("Banco de dados criado.")


@app.cli.command("drop-db")
def drop_db():
    """Remove todas as tabelas do banco de dados."""
    db.drop_all()
    print("Banco de dados removido.")


@app.cli.command("create-admin")
def create_admin():
    """Cria um usuário administrador."""
    username = input("Nome de usuário: ")
    email = input("E-mail: ")
    password = input("Senha: ")

    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    print(f"Usuário '{username}' criado com sucesso.")


if __name__ == '__main__':
    app.run(debug=True)