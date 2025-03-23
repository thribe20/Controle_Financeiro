import os
from datetime import timedelta


class Config:
    """Configurações base para a aplicação"""
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-secreta-padrao-deve-ser-alterada')
    CSRF_ENABLED = True

    # Banco de dados
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB máximo para upload
    UPLOAD_FOLDER = os.path.join('instance', 'uploads')
    ALLOWED_EXTENSIONS = {'ofx'}

    # Sessão
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Bootstrap
    BOOTSTRAP_SERVE_LOCAL = True


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join('instance', 'financasweb-dev.sqlite')


class TestingConfig(Config):
    """Configurações para ambiente de testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join('instance', 'financasweb-test.sqlite')
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Configurações para ambiente de produção"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join('instance', 'financasweb.sqlite')

    # Configurações adicionais para produção
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}