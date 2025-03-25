from datetime import datetime
from app import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(255))
    color = db.Column(db.String(7), default='#3498db')  # Formato HEX
    is_expense = db.Column(db.Boolean, default=True)  # True = despesa, False = receita

    # Relacionamentos
    keywords = db.relationship('CategoryKeyword', backref='category', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Category {self.name}>'


class CategoryKeyword(db.Model):
    __tablename__ = 'category_keywords'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(64), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    match_type = db.Column(db.String(20), default='contains')  # 'contains' ou 'exact'

    def __repr__(self):
        return f'<CategoryKeyword {self.keyword} ({self.match_type})>'


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(128), index=True)  # ID do banco para evitar duplicação
    date = db.Column(db.DateTime, nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))

    # Origem do arquivo
    source_filename = db.Column(db.String(255))

    # Categorização
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category = db.relationship('Category', backref='transactions')

    # Pode ser nullable se você não estiver usando autenticação
    user_id = db.Column(db.Integer, nullable=True)

    # Campos para consulta otimizada
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)

    def __init__(self, **kwargs):
        super(Transaction, self).__init__(**kwargs)
        if 'date' in kwargs:
            self.year = kwargs['date'].year
            self.month = kwargs['date'].month

    @property
    def transaction_type(self):
        return 'receita' if self.amount >= 0 else 'despesa'

    def __repr__(self):
        return f'<Transaction {self.date} {self.amount}>'