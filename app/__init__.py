import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5

# Inicializa extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
bootstrap = Bootstrap5()


def create_app(config_class=None):
    """Cria e configura uma instância da aplicação Flask"""
    app = Flask(__name__, instance_relative_config=True)

    # Carrega configurações padrão
    if config_class is None:
        from app.config import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(config_class)

    # Carrega configurações específicas do ambiente
    if os.path.exists(os.path.join(app.instance_path, 'config.py')):
        app.config.from_pyfile('config.py')

    # Garante que a pasta instance existe
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Inicializa extensões com a aplicação
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bootstrap.init_app(app)

    # Configura login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # Registra blueprints
    from app.routes import auth, dashboard, transactions, categories, reports
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(transactions.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(reports.bp)

    # Registra comandos CLI se houver
    with app.app_context():
        from app import commands

    return app


# Importa modelos para que sejam reconhecidos pelo Flask-Migrate
from app.models import user, transaction, category