# app/services/ofx_parser.py
import os
import hashlib
from datetime import datetime
from ofxparse import OfxParser
from werkzeug.utils import secure_filename
from flask import current_app
from app import db
from app.models.transaction import Transaction
from app.models.uploaded_file import UploadedFile


class OFXImportService:
    """Serviço para importação de arquivos OFX"""

    def __init__(self, user):
        self.user = user

    def allowed_file(self, filename):
        """Verifica se o arquivo possui uma extensão permitida"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

    def save_file(self, file):
        """Salva o arquivo no sistema de arquivos e retorna o nome do arquivo salvo"""
        if not self.allowed_file(file.filename):
            raise ValueError("Tipo de arquivo não permitido. Apenas arquivos OFX são aceitos.")

        # Cria diretório de upload se não existir
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(self.user.id))
        os.makedirs(upload_folder, exist_ok=True)

        # Cria nome seguro para o arquivo
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        saved_filename = f"{timestamp}_{filename}"

        # Salva o arquivo
        file_path = os.path.join(upload_folder, saved_filename)
        file.save(file_path)

        # Calcula hash do arquivo para detectar duplicatas
        file_hash = self._calculate_file_hash(file_path)

        # Verifica se o arquivo já foi importado
        existing_file = UploadedFile.query.filter_by(
            user_id=self.user.id,
            file_hash=file_hash
        ).first()

        if existing_file:
            # Remove o arquivo duplicado
            os.remove(file_path)
            raise ValueError(f"Este arquivo já foi importado em {existing_file.upload_date}")

        # Registra o arquivo no banco de dados
        uploaded_file = UploadedFile(
            user_id=self.user.id,
            filename=saved_filename,
            original_filename=file.filename,
            file_size=os.path.getsize(file_path),
            file_hash=file_hash
        )

        db.session.add(uploaded_file)
        db.session.commit()

        return uploaded_file, file_path

    def _calculate_file_hash(self, file_path):
        """Calcula o hash SHA-256 do arquivo"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def import_transactions(self, file):
        """Importa transações de um arquivo OFX"""
        uploaded_file, file_path = self.save_file(file)

        try:
            # Parsear o arquivo OFX
            with open(file_path, 'rb') as f:
                ofx = OfxParser.parse(f)

            # Extrair as transações
            account = ofx.account
            transactions_imported = 0
            min_date = None
            max_date = None

            # Importar cada transação
            for ofx_transaction in account.statement.transactions:
                # Verificar se a transação já existe
                existing = Transaction.query.filter_by(
                    user_id=self.user.id,
                    external_id=ofx_transaction.id
                ).first()

                if existing:
                    continue

                # Criar nova transação
                transaction = Transaction(
                    user_id=self.user.id,
                    external_id=ofx_transaction.id,
                    date=ofx_transaction.date,
                    amount=float(ofx_transaction.amount),
                    description=ofx_transaction.memo or ofx_transaction.payee,
                    source_filename=uploaded_file.filename,
                    year=ofx_transaction.date.year,
                    month=ofx_transaction.date.month
                )

                # Auto-categorização será feita pelo TransactionService

                db.session.add(transaction)
                transactions_imported += 1

                # Atualizar datas mínimas e máximas para estatísticas
                if min_date is None or ofx_transaction.date < min_date:
                    min_date = ofx_transaction.date
                if max_date is None or ofx_transaction.date > max_date:
                    max_date = ofx_transaction.date

            # Atualizar estatísticas do arquivo importado
            uploaded_file.transactions_count = transactions_imported
            uploaded_file.start_date = min_date
            uploaded_file.end_date = max_date
            uploaded_file.status = 'imported'

            db.session.commit()

            # Categorizar transações recém-importadas
            from app.services.transaction_service import TransactionService
            tx_service = TransactionService(self.user)
            tx_service.auto_categorize_all()

            return transactions_imported

        except Exception as e:
            db.session.rollback()

            # Registrar falha
            uploaded_file.status = 'failed'
            db.session.commit()

            raise e


# app/services/transaction_service.py
from sqlalchemy import extract, func, and_, or_
from app import db
from app.models.transaction import Transaction
from app.models.category import Category, CategoryKeyword


class TransactionService:
    """Serviço para gerenciamento de transações"""

    def __init__(self, user):
        self.user = user

    def get_by_id(self, transaction_id):
        """Busca uma transação pelo ID"""
        return Transaction.query.filter_by(
            id=transaction_id,
            user_id=self.user.id
        ).first()

    def get_by_period(self, year=None, month=None, category_id=None):
        """Busca transações por período e opcionalmente por categoria"""
        query = Transaction.query.filter_by(user_id=self.user.id)

        if year:
            query = query.filter(Transaction.year == year)
        if month:
            query = query.filter(Transaction.month == month)
        if category_id:
            query = query.filter(Transaction.category_id == category_id)

        return query.order_by(Transaction.date.desc()).all()

    def get_monthly_summary(self, year=None):
        """Retorna um resumo mensal de todas as transações, agrupadas por mês e categoria"""
        query = db.session.query(
            Transaction.year,
            Transaction.month,
            Category.name.label('category_name'),
            func.sum(Transaction.amount).label('total_amount')
        ).join(
            Category, Transaction.category_id == Category.id, isouter=True
        ).filter(
            Transaction.user_id == self.user.id
        ).group_by(
            Transaction.year,
            Transaction.month,
            Category.name
        )

        if year:
            query = query.filter(Transaction.year == year)

        return query.order_by(
            Transaction.year,
            Transaction.month,
            Category.name
        ).all()

    def update_category(self, transaction_id, category_id):
        """Atualiza a categoria de uma transação"""
        transaction = self.get_by_id(transaction_id)
        if not transaction:
            return False

        # Verificar se a categoria existe e pertence ao usuário
        if category_id:
            category = Category.query.filter_by(
                id=category_id,
                user_id=self.user.id
            ).first()

            if not category:
                return False

        transaction.category_id = category_id
        db.session.commit()
        return True

    def update_notes(self, transaction_id, notes):
        """Atualiza as notas de uma transação"""
        transaction = self.get_by_id(transaction_id)
        if not transaction:
            return False

        transaction.notes = notes
        db.session.commit()
        return True

    def reconcile(self, transaction_id, reconciled=True):
        """Marca uma transação como conferida"""
        transaction = self.get_by_id(transaction_id)
        if not transaction:
            return False

        transaction.is_reconciled = reconciled
        db.session.commit()
        return True

    def auto_categorize_all(self, recategorize_all=False):
        """
        Categoriza automaticamente todas as transações baseado nas palavras-chave

        Args:
            recategorize_all (bool): Se True, recategoriza todas as transações,
                                     caso contrário, apenas as sem categoria
        """
        # Buscar todas as categorias do usuário e suas palavras-chave
        categories = {}
        for category in Category.query.filter_by(user_id=self.user.id).all():
            keywords = [kw.keyword.lower() for kw in category.keywords]
            categories[category.id] = {
                'name': category.name,
                'keywords': keywords,
                'is_expense': category.is_expense
            }

        # Buscar transações para categorizar
        query = Transaction.query.filter_by(user_id=self.user.id)
        if not recategorize_all:
            query = query.filter(Transaction.category_id == None)

        transactions = query.all()
        categorized_count = 0

        for transaction in transactions:
            # Pré-selecionar categoria base no tipo (receita/despesa)
            is_expense = transaction.amount < 0

            # Para receitas, buscar apenas categorias de receita
            matched_category_id = None

            # Verificar palavras-chave nas descrições
            description = transaction.description.lower() if transaction.description else ""

            for category_id, category_data in categories.items():
                # Verificar se o tipo bate (receita/despesa)
                if is_expense != category_data['is_expense']:
                    continue

                # Verificar se alguma palavra-chave está na descrição
                for keyword in category_data['keywords']:
                    if keyword and keyword in description:
                        matched_category_id = category_id
                        break

                if matched_category_id:
                    break

            # Atualizar a categoria se encontrou correspondência
            if matched_category_id:
                transaction.category_id = matched_category_id
                categorized_count += 1

        db.session.commit()
        return categorized_count


# app/services/category_service.py
from app import db
from app.models.category import Category, CategoryKeyword
from app.models.transaction import Transaction
from sqlalchemy import func


class CategoryService:
    """Serviço para gerenciamento de categorias"""

    def __init__(self, user):
        self.user = user

    def get_all(self):
        """Retorna todas as categorias do usuário"""
        return Category.query.filter_by(user_id=self.user.id).order_by(Category.name).all()

    def get_by_id(self, category_id):
        """Busca uma categoria pelo ID"""
        return Category.query.filter_by(
            id=category_id,
            user_id=self.user.id
        ).first()

    def create(self, name, description=None, color=None, is_expense=True):
        """Cria uma nova categoria"""
        # Verificar se já existe uma categoria com o mesmo nome
        existing = Category.query.filter_by(
            name=name,
            user_id=self.user.id
        ).first()

        if existing:
            return None

        category = Category(
            name=name,
            description=description,
            color=color,
            is_expense=is_expense,
            user_id=self.user.id
        )

        db.session.add(category)
        db.session.commit()
        return category

    def update(self, category_id, name=None, description=None, color=None, is_expense=None):
        """Atualiza uma categoria existente"""
        category = self.get_by_id(category_id)
        if not category:
            return False

        if name and name != category.name:
            # Verificar se já existe outra categoria com o mesmo nome
            existing = Category.query.filter_by(
                name=name,
                user_id=self.user.id
            ).first()

            if existing and existing.id != category_id:
                return False

            category.name = name

        if description is not None:
            category.description = description

        if color:
            category.color = color

        if is_expense is not None:
            category.is_expense = is_expense

        db.session.commit()
        return True

    def delete(self, category_id):
        """Remove uma categoria"""
        category = self.get_by_id(category_id)
        if not category:
            return False

        # Remover categoria das transações que a usam
        Transaction.query.filter_by(
            category_id=category_id
        ).update({Transaction.category_id: None})

        # Remover a categoria
        db.session.delete(category)
        db.session.commit()
        return True

    def add_keyword(self, category_id, keyword):
        """Adiciona uma palavra-chave a uma categoria"""
        category = self.get_by_id(category_id)
        if not category:
            return False

        # Verificar se a palavra-chave já existe
        existing = CategoryKeyword.query.filter_by(
            category_id=category_id,
            keyword=keyword
        ).first()

        if existing:
            return False

        keyword_obj = CategoryKeyword(
            keyword=keyword,
            category_id=category_id
        )

        db.session.add(keyword_obj)
        db.session.commit()
        return True

    def remove_keyword(self, keyword_id):
        """Remove uma palavra-chave de uma categoria"""
        keyword = CategoryKeyword.query.filter_by(id=keyword_id).first()

        if not keyword or keyword.category.user_id != self.user.id:
            return False

        db.session.delete(keyword)
        db.session.commit()
        return True

    def get_stats(self):
        """Retorna estatísticas sobre as categorias do usuário"""
        # Total de transações por categoria
        transactions_by_category = db.session.query(
            Category.id,
            Category.name,
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_amount')
        ).outerjoin(
            Transaction, Transaction.category_id == Category.id
        ).filter(
            Category.user_id == self.user.id
        ).group_by(
            Category.id
        ).all()

        # Percentual de transações categorizadas
        total_transactions = Transaction.query.filter_by(user_id=self.user.id).count()
        categorized = Transaction.query.filter(
            Transaction.user_id == self.user.id,
            Transaction.category_id != None
        ).count()

        categorization_rate = (categorized / total_transactions * 100) if total_transactions > 0 else 0

        return {
            'by_category': transactions_by_category,
            'total_transactions': total_transactions,
            'categorized_transactions': categorized,
            'categorization_rate': categorization_rate
        }


# app/services/report_service.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import os
from datetime import datetime
from sqlalchemy import func, extract, desc
from app import db
from app.models.transaction import Transaction
from app.models.category import Category


class ReportService:
    """Serviço para geração de relatórios e gráficos"""

    def __init__(self, user):
        self.user = user

    def generate_monthly_summary(self, year=None, as_dataframe=False):
        """
        Gera um resumo mensal de receitas e despesas

        Args:
            year (int): Ano para filtrar, ou None para todos
            as_dataframe (bool): Se True, retorna um DataFrame pandas

        Returns:
            list ou DataFrame: Dados do resumo mensal
        """
        query = db.session.query(
            Transaction.year,
            Transaction.month,
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.user_id == self.user.id
        ).group_by(
            Transaction.year,
            Transaction.month
        )

        if year:
            query = query.filter(Transaction.year == year)

        result = query.order_by(
            Transaction.year,
            Transaction.month
        ).all()

        # Transformar em DataFrame se solicitado
        if as_dataframe:
            df = pd.DataFrame(result, columns=['year', 'month', 'total_amount'])
            df['period'] = df.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
            return df

        return result

    def generate_category_summary(self, year=None, month=None, as_dataframe=False):
        """
        Gera um resumo de transações por categoria

        Args:
            year (int): Ano para filtrar, ou None para todos
            month (int): Mês para filtrar, ou None para todos
            as_dataframe (bool): Se True, retorna um DataFrame pandas

        Returns:
            list ou DataFrame: Dados do resumo por categoria
        """
        query = db.session.query(
            Category.id,
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label('total_amount'),
            func.count(Transaction.id).label('transaction_count')
        ).outerjoin(
            Category, Transaction.category_id == Category.id
        ).filter(
            Transaction.user_id == self.user.id
        )

        if year:
            query = query.filter(Transaction.year == year)
        if month:
            query = query.filter(Transaction.month == month)

        query = query.group_by(
            Category.id
        ).order_by(
            func.abs(func.sum(Transaction.amount)).desc()
        )

        result = query.all()

        # Transformar em DataFrame se solicitado
        if as_dataframe:
            df = pd.DataFrame(result, columns=[
                'category_id', 'category_name', 'category_color',
                'total_amount', 'transaction_count'
            ])
            return df

        return result

    def plot_monthly_expenses(self, year=None):
        """
        Gera um gráfico de despesas mensais por categoria

        Args:
            year (int): Ano para filtrar, ou None para o ano atual

        Returns:
            bytes: Imagem do gráfico em formato PNG
        """
        if year is None:
            year = datetime.now().year

        # Obter dados agrupados por mês e categoria
        query = db.session.query(
            Transaction.month,
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label('total')
        ).join(
            Category, Transaction.category_id == Category.id
        ).filter(
            Transaction.user_id == self.user.id,
            Transaction.year == year,
            Transaction.amount < 0  # Apenas despesas
        ).group_by(
            Transaction.month,
            Category.id
        ).order_by(
            Transaction.month,
            Category.name
        )

        results = query.all()

        # Converter para DataFrame
        df = pd.DataFrame(results, columns=['month', 'category', 'color', 'amount'])
        df['amount'] = df['amount'].abs()  # Converter para valores positivos

        # Criar um mapa de meses para exibição mais amigável
        month_names = {
            1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
            7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
        }
        df['month_name'] = df['month'].map(month_names)

        # Verificar se há dados para plotar
        if df.empty:
            # Criar uma imagem em branco com mensagem
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, "Sem dados para exibir",
                     horizontalalignment='center', verticalalignment='center',
                     transform=plt.gca().transAxes, fontsize=14)
            plt.axis('off')
        else:
            # Pivotar DataFrame para formato adequado para gráfico de barras empilhadas
            pivot_df = df.pivot_table(
                index='month_name',
                columns='category',
                values='amount',
                aggfunc='sum'
            ).fillna(0)

            # Ordenar meses cronologicamente
            pivot_df = pivot_df.reindex([month_names[i] for i in range(1, 13) if month_names[i] in pivot_df.index])

            # Criar o gráfico
            plt.figure(figsize=(12, 8))
            pivot_df.plot(kind='bar', stacked=True, ax=plt.gca(), figsize=(12, 8))

            plt.title(f'Despesas Mensais por Categoria - {year}', fontsize=16)
            plt.xlabel('Mês', fontsize=12)
            plt.ylabel('Valor (R$)', fontsize=12)
            plt.legend(title='Categoria', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Salvar o gráfico em um buffer de bytes
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()

        buf.seek(0)
        return buf.getvalue()

    def plot_category_breakdown(self, year=None, month=None):
        """
        Gera um gráfico de pizza com a distribuição de despesas por categoria

        Args:
            year (int): Ano para filtrar, ou None para o ano atual
            month (int): Mês para filtrar, ou None para todos os meses do ano

        Returns:
            bytes: Imagem do gráfico em formato PNG
        """
        if year is None:
            year = datetime.now().year

        # Construir a query
        query = db.session.query(
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label('total')
        ).join(
            Category, Transaction.category_id == Category.id
        ).filter(
            Transaction.user_id == self.user.id,
            Transaction.year == year,
            Transaction.amount < 0  # Apenas despesas
        )

        if month:
            query = query.filter(Transaction.month == month)

        query = query.group_by(
            Category.id
        ).order_by(
            func.sum(Transaction.amount)
        )

        results = query.all()

        # Converter para DataFrame
        df = pd.DataFrame(results, columns=['category', 'color', 'amount'])
        df['amount'] = df['amount'].abs()  # Converter para valores positivos

        # Verificar se há dados para plotar
        if df.empty:
            # Criar uma imagem em branco com mensagem
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, "Sem dados para exibir",
                     horizontalalignment='center', verticalalignment='center',
                     transform=plt.gca().transAxes, fontsize=14)
            plt.axis('off')
        else:
            # Configurar o gráfico
            plt.figure(figsize=(10, 8))

            # Usar as cores definidas para as categorias, se disponíveis
            colors = df['color'].tolist() if not df['color'].isnull().any() else None

            plt.pie(
                df['amount'],
                labels=df['category'],
                autopct='%1.1f%%',
                startangle=90,
                shadow=False,
                colors=colors
            )

            # Título
            title = 'Distribuição de Despesas por Categoria'
            if month:
                title += f' ({month}/{year})'
            else:
                title += f' ({year})'

            plt.title(title, fontsize=16)
            plt.axis('equal')  # Equal aspect ratio

        # Salvar o gráfico em um buffer de bytes
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()

        buf.seek(0)
        return buf.getvalue()

    def plot_income_vs_expenses(self, year=None):
        """
        Gera um gráfico comparando receitas e despesas ao longo do tempo

        Args:
            year (int): Ano para filtrar, ou None para todos

        Returns:
            bytes: Imagem do gráfico em formato PNG
        """
        # Construir query para receitas
        income_query = db.session.query(
            Transaction.year,
            Transaction.month,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == self.user.id,
            Transaction.amount > 0  # Apenas receitas
        )

        if year:
            income_query = income_query.filter(Transaction.year == year)

        income_query = income_query.group_by(
            Transaction.year,
            Transaction.month
        ).order_by(
            Transaction.year,
            Transaction.month
        )

        # Construir query para despesas
        expense_query = db.session.query(
            Transaction.year,
            Transaction.month,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == self.user.id,
            Transaction.amount < 0  # Apenas despesas
        )

        if year:
            expense_query = expense_query.filter(Transaction.year == year)

        expense_query = expense_query.group_by(
            Transaction.year,
            Transaction.month
        ).order_by(
            Transaction.year,
            Transaction.month
        )

        # Executar as queries
        income_results = income_query.all()
        expense_results = expense_query.all()

        # Converter para DataFrames
        income_df = pd.DataFrame(income_results, columns=['year', 'month', 'amount'])
        expense_df = pd.DataFrame(expense_results, columns=['year', 'month', 'amount'])

        # Adicionar coluna de período
        income_df['period'] = income_df.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
        expense_df['period'] = expense_df.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)

        # Tornar as despesas positivas para visualização
        expense_df['amount'] = expense_df['amount'].abs()

        # Verificar se há dados para plotar
        if income_df.empty and expense_df.empty:
            # Criar uma imagem em branco com mensagem
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, "Sem dados para exibir",
                     horizontalalignment='center', verticalalignment='center',
                     transform=plt.gca().transAxes, fontsize=14)
            plt.axis('off')
        else:
            # Obter todos os períodos únicos
            all_periods = sorted(set(income_df['period'].tolist() + expense_df['period'].tolist()))

            # Criar um DataFrame para o gráfico
            plot_df = pd.DataFrame({'period': all_periods})

            # Mesclar com receitas e despesas
            plot_df = pd.merge(plot_df, income_df[['period', 'amount']],
                               on='period', how='left').rename(columns={'amount': 'receitas'})
            plot_df = pd.merge(plot_df, expense_df[['period', 'amount']],
                               on='period', how='left').rename(columns={'amount': 'despesas'})

            # Preencher valores NaN com 0
            plot_df.fillna(0, inplace=True)

            # Calcular o saldo
            plot_df['saldo'] = plot_df['receitas'] - plot_df['despesas']

            # Configurar o gráfico
            plt.figure(figsize=(12, 7))

            # Barras para receitas e despesas
            bar_width = 0.35
            x = range(len(plot_df))

            plt.bar([i - bar_width / 2 for i in x], plot_df['receitas'],
                    width=bar_width, label='Receitas', color='green', alpha=0.7)

            plt.bar([i + bar_width / 2 for i in x], plot_df['despesas'],
                    width=bar_width, label='Despesas', color='red', alpha=0.7)

            # Linha para o saldo
            plt.plot(x, plot_df['saldo'], 'bo-', label='Saldo', linewidth=2)

            # Adicionar linha do zero para referência
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)

            # Configurações de eixos e legendas
            title = 'Receitas vs Despesas'
            if year:
                title += f' ({year})'

            plt.title(title, fontsize=16)
            plt.xlabel('Mês', fontsize=12)
            plt.ylabel('Valor (R$)', fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.xticks(x, plot_df['period'], rotation=45)
            plt.legend()

        # Salvar o gráfico em um buffer de bytes
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        plt.close()

        buf.seek(0)
        return buf.getvalue()