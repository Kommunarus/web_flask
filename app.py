import json
import os
import time

from flask import json, send_file
from flask_caching import Cache
import cv2

import uuid
from flask import Flask, request, jsonify
import logging
import pandas as pd

from flask_sqlalchemy import SQLAlchemy

from flask_migrate import Migrate

from config import Config
#from forms import cam_choices
from functionCV import getImagesPreview
from visual import plotGraf

from VDT.main import startODaTr
from threading import Thread

from threading import Thread
from matplotlib.pyplot import figure

import pymysql
from pymysql.cursors import DictCursor

from flask import render_template, url_for, redirect, request
from forms import IndexForm, previewForm, CameraForm

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config.from_object(Config)

# change to "redis" and restart to cache again

# some time later
cache = Cache(config={'CACHE_TYPE': 'simple'})

cache.init_app(app)
with app.app_context():
    cache.clear()

db = SQLAlchemy(app)
migrate = Migrate(app, db)

connection = pymysql.connect(
    host='localhost',
    user='kommunar',
    password='123',
    db='web_slake',
    charset='utf8mb4',
    cursorclass=DictCursor
)

rec = 0
max_reg = 1
currentCam = ''

counterFrame = 1

totalObject = False
partObject = False
timePartObject = False
freqFrame = 5
lineObject = False
mapTrajectory = False
countFrame = 150

cam_link = {'cam1':'https://rtsp.me/embed/tYYdKhk9/', 'cam2': 'https://rtsp.me/embed/btDytRDe/', 'cam3':'https://rtsp.me/embed/fbsyiFAd/'}

fig1 = figure()
fig2 = figure()

folderDec = '../static/images/processing/'
folderCam = '../static/images/cam/'

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

class TableRegion(db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    region              = db.Column(db.Integer, index=True)
    x_coordinate        = db.Column(db.Integer)
    y_coordinate        = db.Column(db.Integer)


@app.route('/',  methods=['GET'])
@app.route('/index', methods=['GET'])
def index():

    form = IndexForm()
    if form.validate_on_submit():
        if form.submit.data:
            return redirect(url_for('camera'))
    return render_template('index.html',  form=form)

@app.route('/camera', methods=['GET', 'POST'])
def camera():

    form = CameraForm()
    if form.validate_on_submit():
        if form.next_button1.data:
            web_select = cam_link['cam1']
            return redirect(url_for('preview', webcam = 'cam1'))
        if form.next_button2.data:
            web_select = cam_link['cam2']
            return redirect(url_for('preview', webcam = 'cam2'))
        if form.next_button3.data:
            web_select = cam_link['cam3']
            return redirect(url_for('preview', webcam = 'cam3'))

    image_src1 = 'images/visual/cam1.png'
    image_src2 = 'images/visual/cam2.png'
    image_src3 = 'images/visual/cam3.png'

    return render_template('camera.html', title='Камеры', images1=image_src1, images2=image_src2, images3=image_src3, form = form )

@app.route('/preview', methods=['GET', 'POST'])
def preview():

    global currentCam
    global totalObject
    global partObject
    global timePartObject
    global freqFrame
    global lineObject
    global mapTrajectory
    global countFrame

    form = previewForm()


    if request.method == "GET":
        webcam = request.args.get('webcam')
        VIDEO_URL = getImagesPreview(cam_link[webcam])
        currentCam = VIDEO_URL
    if request.method == "POST":
        totalObject = form.totalObject.data
        partObject = form.partObject.data
        timePartObject = form.timePartObject.data
        freqFrame = form.freqFrame.data
        lineObject = form.lineObject.data
        mapTrajectory = form.mapTrajectory.data
        countFrame = form.countFrame.data
    if form.validate_on_submit():
        return redirect(url_for('indicators'))
    df = pd.read_sql(sql=db.session.query(TableRegion).with_entities(TableRegion.region, TableRegion.x_coordinate,
                                                                     TableRegion.y_coordinate).statement,
                     con=db.session.bind)
    return render_template('preview.html', form=form, tables = [df.to_html(header="true")])

@app.route('/_ajax_user_input')
def ajax_user_input():
     global user_input
     user_input = request.args.get('user_input', 0, type=int)
     return "ok"

@app.route('/results/<uuid>', methods=['GET', 'POST'])
def results(uuid):
    data = get_file_content(uuid)
    return render_template('results.html',  data=data)

def get_file_content(uuid):
    with open('static/images/'+uuid+'.csv', 'r') as file:
        return file.read()



@app.route('/saveRegion', methods = ['GET', 'POST'])
def saveRegion():
    global max_reg

    if rec == 1:
        jsdata = json.loads(request.form['canvas_data'])

        x = round(jsdata[0],0)
        y = round(jsdata[1],0)
        inTable = TableRegion.query.filter_by(x_coordinate=x, y_coordinate=y).first()

        if inTable is None:
            coordinate = TableRegion(region=max_reg, x_coordinate=x, y_coordinate=y)
            db.session.add(coordinate)
            db.session.commit()

            query = "INSERT INTO web_slake.table_region(region, x, y) " \
                    "VALUES(%s,%s,%s)"
            args = (int(max_reg), int(x), int(y))
            cursor = connection.cursor()
            cursor.execute(query, args)
            connection.commit()


@app.route('/clearRegion', methods = ['GET', 'POST'])
def clearRegion():
    global max_reg
    try:
        db.session.query(TableRegion).delete()
        db.session.commit()

        max_reg = 1
    except:
        db.session.rollback()

    query = "DELETE FROM web_slake.table_region"
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()

    df = pd.read_sql(sql = db.session.query(TableRegion).with_entities(TableRegion.region, TableRegion.x_coordinate, TableRegion.y_coordinate).statement, con = db.session.bind)
    return render_template('_table.html', tables=[df.to_html(header="true")])

@app.route('/ReadTableCoordinate', methods = ['GET', 'POST'])
def ReadTableCoordinate():
    df = pd.read_sql(sql = db.session.query(TableRegion).with_entities(TableRegion.region, TableRegion.x_coordinate, TableRegion.y_coordinate).statement, con = db.session.bind)
    return render_template('_table.html', tables = [df.to_html(header="true")])

@app.route('/setRec', methods = ['GET', 'POST'])
def setRec():
    global rec, max_reg
    max_reg = db.session.query(db.func.max(TableRegion.region)).scalar()
    if max_reg is None:
        max_reg = 1
    else:
        max_reg += 1

    if rec == 0:
        rec = 1
        textRec = 'Rec'
    else:
        rec = 0
        textRec = ''
    return render_template('_setRec.html', rec = textRec)



@app.route('/indicators', methods=['GET', 'POST'])
def indicators():

    # Загрузка кадров
    #rec()
    thr_rec = Thread(target=run_async_func_rec)
    thr_rec.start()

    # Детектирование и запись в скл
    time.sleep(10)
    data = ( folderCam, folderDec, countFrame)
    thr = Thread(target=run_async_func, args=data)
    thr.start()
    # Визаулизация
    # сейчас она связана с js в get_image

    return render_template('indicators.html')

def run_async_func_rec():
    print('Start rec')
    rec_img()
    print('End rec')


def run_async_func(x,y, count):
    print('Start detect')
    startODaTr(x, y, count)
    print('End detect')


def rec_img():

    global currentCam
    print('countFrame: {}'.format(countFrame))
    folder = folderCam
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)
    folder2 = folderDec
    for the_file in os.listdir(folder2):
        file_path = os.path.join(folder2, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    cap = cv2.VideoCapture(currentCam)
    tot = 0

    while (True):
        ret, frame = cap.read()

        tot += 1
        if ret:
            cv2.imwrite(folder + str(tot-1) + '.jpg', frame)

        if tot == countFrame:
            break

@app.route("/liveWeb")
def liveWeb():
    return render_template('liveWeb.html',)


@app.route('/get_liveCam', methods=['GET'])
def get_liveCam():

    global counterFrame

    counterFrame += 1
    if counterFrame > len(os.listdir(folderDec)):
        counterFrame = 1

    image_src = 'images/processing/{}.jpg'.format(str(counterFrame))

    return render_template('get_liveCam.html', title='Доска', images=image_src, rows=counterFrame, )

@app.route('/get_plot', methods=['GET'])
def get_plot():

    fig = plotGraf(totalObject, partObject, timePartObject, freqFrame, lineObject, mapTrajectory)

    return render_template('_indicatorPlot.html',title='Доска',fig = fig)


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000)
    #startODaTr(folderCam, folderDec)
    app.run(debug=True, use_reloader=False)