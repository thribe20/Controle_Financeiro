# FinançasWeb - Sistema de Análise de Contas Pessoais

FinançasWeb é uma aplicação web para análise e gerenciamento de contas pessoais. Ele permite importar extratos bancários no formato OFX (Open Financial Exchange), categorizar transações automaticamente e gerar relatórios visuais para uma melhor compreensão das suas finanças.

## Principais Funcionalidades

- **Importação de Arquivos OFX**: Importe extratos de diversos bancos no formato OFX
- **Categorização Automática**: Transações são categorizadas automaticamente com base em palavras-chave
- **Dashboard Interativo**: Visualize suas finanças com gráficos e indicadores
- **Relatórios Detalhados**: Acesse relatórios de despesas mensais, distribuição por categoria e muito mais
- **Exportação CSV**: Exporte seus dados para análise em outras ferramentas
- **Multi-usuário**: Cada usuário tem acesso apenas aos seus próprios dados

## Tecnologias Utilizadas

- **Backend**: Python 3.9+ com Flask
- **Banco de Dados**: SQLAlchemy (suporta SQLite, PostgreSQL, MySQL)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Visualização de Dados**: Chart.js, Matplotlib
- **Análise de Dados**: Pandas, NumPy
- **Segurança**: Flask-Login, Flask-WTF

## Instalação

### Pré-requisitos

- Python 3.9 ou superior
- pip (gerenciador de pacotes do Python)
- Ambiente virtual (opcional, mas recomendado)

### Instalação Local

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/financasweb.git
   cd financasweb
   ```

2. Crie e ative um ambiente virtual (opcional):
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   ```
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

5. Inicialize o banco de dados:
   ```
   flask create-db
   ```

6. Execute a aplicação:
   ```
   flask run
   ```

7. Acesse a aplicação em seu navegador:
   ```
   http://localhost:5000
   ```

### Deployment em Produção

Para um ambiente de produção, é recomendado:

1. Usar um servidor WSGI como Gunicorn ou uWSGI
2. Configurar um proxy reverso como Nginx ou Apache
3. Utilizar um banco de dados mais robusto (PostgreSQL)
4. Ativar HTTPS com certificados SSL

Exemplo de configuração com Gunicorn e Nginx:

```bash
# Instalar Gunicorn
pip install gunicorn

# Executar com Gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
```

## Estrutura do Projeto

```
financasweb/                 # Diretório raiz do projeto
│
├── app/                    # Código da aplicação
│   ├── __init__.py         # Inicializa a aplicação Flask
│   ├── config.py           # Configurações da aplicação
│   ├── models/             # Modelos de dados
│   ├── services/           # Lógica de negócio 
│   ├── routes/             # Rotas da aplicação
│   ├── static/             # Arquivos estáticos
│   └── templates/          # Templates HTML
│
├── migrations/             # Migrações do banco de dados
├── instance/               # Instância da aplicação (configs locais, DB)
├── logs/                   # Arquivos de log
├── tests/                  # Testes automatizados
├── run.py                  # Script para iniciar a aplicação
├── requirements.txt        # Dependências do projeto
├── .env.example            # Exemplo de variáveis de ambiente
└── README.md               # Documentação do projeto
```

## Uso

### Importando Extratos

1. Faça login na aplicação
2. Vá para "Transações" > "Importar OFX"
3. Selecione um arquivo OFX do seu banco
4. Clique em "Importar"

### Gerenciando Categorias

1. Vá para "Categorias"
2. Adicione novas categorias conforme necessário
3. Configure palavras-chave para categorização automática

### Visualizando Relatórios

1. Vá para "Relatórios"
2. Selecione o tipo de relatório desejado
3. Filtre por ano/mês conforme necessário
4. Visualize ou exporte os dados

## Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das suas alterações (`git commit -am 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

Para dúvidas, sugestões ou suporte, entre em contato por email ou abra uma issue no repositório.