import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Criar a extensão do banco de dados
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Configurações básicas
    app.config['SECRET_KEY'] = 'chave-secreta-temporaria'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///financas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configuração para upload de arquivos
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB máximo
    app.config['UPLOAD_FOLDER'] = os.path.join('instance', 'uploads')

    # Inicializar extensões
    db.init_app(app)

    # Criar pastas necessárias
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Importar blueprints
    with app.app_context():
        from app.routes.main import main_bp
        from app.routes.transactions import transaction_bp
        from app.routes.categories import category_bp
        from app.routes.reports import reports_bp  # Novo blueprint de relatórios

        # Registrar blueprints
        app.register_blueprint(main_bp)
        app.register_blueprint(transaction_bp)
        app.register_blueprint(category_bp)
        app.register_blueprint(reports_bp)  # Registrar o novo blueprint

        # Criar tabelas
        db.create_all()

    return app