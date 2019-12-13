from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, FieldList, FormField, SelectField, IntegerField
from wtforms.validators import DataRequired


#cam_choices = [('cam1','https://rtsp.me/embed/tYYdKhk9/'), ('cam2', 'https://www.geocam.ru/online/whsd-ekateringofka/')]
class IndexForm(FlaskForm):
    submit = SubmitField('Далее')

class CameraForm(FlaskForm):
    next_button1 = SubmitField('Первая')
    next_button2 = SubmitField('Вторая')
    next_button3 = SubmitField('Третья')

class previewForm(FlaskForm):
    next_button = SubmitField('Далее')

    totalObject = BooleanField('Количество объектов в кадре', default=True)
    partObject = BooleanField('Количество объектов в областях', default=True)
    timePartObject = BooleanField('Время нахождения объекта в областях', default=True)
    lineObject = BooleanField('Количество пересечений с линиями (области с двумя точками)', default=True)
    mapTrajectory = BooleanField('Карта траекторий', default=True)

    countFrame = IntegerField('Количество кадров для анализа', default=150)
    freqFrame = IntegerField('Частота кадров', default=5)



