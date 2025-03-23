# app/forms/auth_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    """Formulário de login"""
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class RegisterForm(FlaskForm):
    """Formulário de registro"""
    username = StringField('Usuário', validators=[
        DataRequired(),
        Length(min=3, max=64, message='O nome de usuário deve ter entre 3 e 64 caracteres')
    ])
    email = StringField('E-mail', validators=[
        DataRequired(),
        Email(message='E-mail inválido'),
        Length(max=120)
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Registrar')


class ChangePasswordForm(FlaskForm):
    """Formulário para alteração de senha"""
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[
        DataRequired(),
        Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(),
        EqualTo('new_password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Alterar Senha')


# app/forms/transaction_forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional
from datetime import datetime


class TransactionFilterForm(FlaskForm):
    """Formulário para filtrar transações"""
    year = SelectField('Ano', coerce=int)
    month = SelectField('Mês', coerce=int, choices=[
        (0, 'Todos os meses'),
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ])
    category = SelectField('Categoria', coerce=int)
    submit = SubmitField('Filtrar')

    def __init__(self, *args, **kwargs):
        super(TransactionFilterForm, self).__init__(*args, **kwargs)
        # Preencher anos dinamicamente (será feito na rota)
        current_year = datetime.now().year
        self.year.choices = [(y, str(y)) for y in range(current_year - 5, current_year + 1)]


class TransactionEditForm(FlaskForm):
    """Formulário para editar transação"""
    category_id = SelectField('Categoria', coerce=int)
    notes = TextAreaField('Observações', validators=[Optional()])
    is_reconciled = BooleanField('Conferida')
    submit = SubmitField('Salvar')


class UploadForm(FlaskForm):
    """Formulário para upload de arquivo OFX"""
    file = FileField('Arquivo OFX', validators=[
        FileRequired(),
        FileAllowed(['ofx'], 'Apenas arquivos OFX são permitidos')
    ])
    submit = SubmitField('Importar')


# app/forms/category_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class CategoryForm(FlaskForm):
    """Formulário para criar e editar categorias"""
    name = StringField('Nome', validators=[
        DataRequired(),
        Length(min=2, max=64, message='O nome deve ter entre 2 e 64 caracteres')
    ])
    description = TextAreaField('Descrição', validators=[Optional()])
    color = StringField('Cor (HEX)', validators=[
        DataRequired(),
        Length(min=4, max=7, message='Código de cor inválido')
    ], default='#3498db')
    is_expense = BooleanField('É despesa?', default=True)
    submit = SubmitField('Salvar')


class CategoryKeywordForm(FlaskForm):
    """Formulário para adicionar palavras-chave a categorias"""
    keyword = StringField('Palavra-chave', validators=[
        DataRequired(),
        Length(min=2, max=64, message='A palavra-chave deve ter entre 2 e 64 caracteres')
    ])
    submit = SubmitField('Adicionar')


# app/forms/report_forms.py
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import Optional
from datetime import datetime


class ReportFilterForm(FlaskForm):
    """Formulário para filtrar relatórios"""
    year = SelectField('Ano', coerce=int)
    month = SelectField('Mês', coerce=int, choices=[
        (0, 'Todos os meses'),
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ], validators=[Optional()])
    submit = SubmitField('Gerar Relatório')