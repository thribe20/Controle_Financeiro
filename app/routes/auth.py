from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models.user import User
from app.forms.auth_forms import LoginForm, RegisterForm, ChangePasswordForm

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para login de usuários"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Nome de usuário ou senha inválidos', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('dashboard.index')

        return redirect(next_page)

    return render_template('auth/login.html', title='Login', form=form)


@bp.route('/logout')
def logout():
    """Rota para logout de usuários"""
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registro de novos usuários"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Verificar se o nome de usuário já existe
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Este nome de usuário já está em uso.', 'danger')
            return redirect(url_for('auth.register'))

        # Verificar se o email já existe
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Este e-mail já está em uso.', 'danger')
            return redirect(url_for('auth.register'))

        # Criar o novo usuário
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )

        db.session.add(user)
        db.session.commit()

        # Inicializar categorias padrão
        from app.services.category_service import CategoryService
        category_service = CategoryService(user)

        # Categorias de despesas
        category_service.create('Alimentação', 'Supermercados, restaurantes e lanches', '#FF5733', True)
        category_service.create('Transporte', 'Combustível, passagens e táxi/Uber', '#C70039', True)
        category_service.create('Moradia', 'Aluguel, condomínio e contas da casa', '#900C3F', True)
        category_service.create('Saúde', 'Plano de saúde, medicamentos e consultas', '#581845', True)
        category_service.create('Educação', 'Cursos, material escolar e livros', '#FFC300', True)
        category_service.create('Lazer', 'Cinema, viagens e outras diversões', '#DAF7A6', True)
        category_service.create('Vestuário', 'Roupas, calçados e acessórios', '#FFC300', True)
        category_service.create('Outros Gastos', 'Despesas diversas', '#C70039', True)

        # Categorias de receitas
        category_service.create('Salário', 'Remuneração do trabalho', '#2ECC71', False)
        category_service.create('Investimentos', 'Rendimentos de aplicações financeiras', '#27AE60', False)
        category_service.create('Outras Receitas', 'Receitas diversas', '#239B56', False)

        flash('Conta criada com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Cadastro', form=form)


@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Rota para alteração de senha"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Senha atual incorreta.', 'danger')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(form.new_password.data)
        db.session.commit()

        flash('Sua senha foi alterada com sucesso.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/change_password.html', title='Alterar Senha', form=form)