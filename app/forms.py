from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class CategoryForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Descrição', validators=[Optional(), Length(max=255)])
    color = StringField('Cor (HEX)', validators=[DataRequired()], default='#3498db')
    is_expense = BooleanField('É despesa?', default=True)
    submit = SubmitField('Salvar')

class KeywordForm(FlaskForm):
    keyword = StringField('Palavra-chave', validators=[DataRequired(), Length(max=64)])
    match_type = SelectField('Tipo de Correspondência',
                             choices=[('contains', 'Contém'), ('exact', 'É exatamente')],
                             default='contains')
    submit = SubmitField('Adicionar')

class UploadForm(FlaskForm):
    file = FileField('Arquivo OFX', validators=[
        FileRequired(),
        FileAllowed(['ofx'], 'Apenas arquivos OFX são permitidos')
    ])
    submit = SubmitField('Importar')