# app/models/user.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    """Modelo para usuários do sistema"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relações
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    categories = db.relationship('Category', backref='user', lazy='dynamic')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        """Define a senha criptografada para o usuário"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde à senha armazenada"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Função auxiliar para carregar o usuário pelo ID para o Flask-Login"""
    return User.query.get(int(user_id))


# app/models/category.py
from datetime import datetime
from app import db


class Category(db.Model):
    """Modelo para categorias de transações"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255))
    color = db.Column(db.String(7), default='#3498db')  # Formato HEX
    is_expense = db.Column(db.Boolean, default=True)  # True = despesa, False = receita
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Chave estrangeira para usuário
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relações
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')
    keywords = db.relationship('CategoryKeyword', backref='category', lazy='dynamic',
                               cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('name', 'user_id', name='_category_user_uc'),
    )

    def __repr__(self):
        return f'<Category {self.name}>'


class CategoryKeyword(db.Model):
    """Modelo para palavras-chave de categorias"""
    __tablename__ = 'category_keywords'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(64), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('keyword', 'category_id', name='_keyword_category_uc'),
    )

    def __repr__(self):
        return f'<CategoryKeyword {self.keyword}>'


# app/models/transaction.py
from datetime import datetime
from app import db


class Transaction(db.Model):
    """Modelo para transações financeiras"""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(128), index=True)  # ID vindo do banco (para evitar duplicatas)
    date = db.Column(db.DateTime, nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    notes = db.Column(db.Text)
    is_reconciled = db.Column(db.Boolean, default=False)  # Se foi conferida pelo usuário

    # Origem do arquivo
    source_filename = db.Column(db.String(255))
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Chaves estrangeiras
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    # Campos calculados (para otimização de consultas)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    def __init__(self, **kwargs):
        super(Transaction, self).__init__(**kwargs)
        if self.date:
            self.year = self.date.year
            self.month = self.date.month

    @property
    def transaction_type(self):
        """Retorna 'receita' se valor for positivo ou 'despesa' se negativo"""
        return 'receita' if self.amount >= 0 else 'despesa'

    def __repr__(self):
        return f'<Transaction {self.date} {self.amount} {self.description}>'


# app/models/uploaded_file.py
from datetime import datetime
from app import db


class UploadedFile(db.Model):
    """Modelo para arquivos OFX importados"""
    __tablename__ = 'uploaded_files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # Tamanho em bytes
    file_hash = db.Column(db.String(64), index=True)  # Hash do arquivo para detectar duplicatas
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='imported')  # imported, failed, etc.

    # Estatísticas
    transactions_count = db.Column(db.Integer, default=0)
    start_date = db.Column(db.DateTime)  # Data da transação mais antiga
    end_date = db.Column(db.DateTime)  # Data da transação mais recente

    # Chave estrangeira para usuário
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<UploadedFile {self.original_filename}>'