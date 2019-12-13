from lxml import etree
from io import StringIO
import requests
import cv2
import datetime
import time
import pymysql
from pymysql.cursors import DictCursor
import pandas as pd
import numpy as np




def get_links(tree):
    # This will get the anchor tags <a href...>
    refs = tree.xpath("//script")
    # Get the url from the ref
    links = [link.text for link in refs]
    # Return a list that only ends with .com.br
    return [l for l in links if (l != None and l.find('.m3u8') != -1)]

def getLinkPreview(web):
    # Set explicit HTMLParser
    parser = etree.HTMLParser()

    page = requests.get(web)

    # Decode the page content from bytes to string
    html = page.content.decode("utf-8")

    # Create your etree with a StringIO object which functions similarly
    # to a fileHandler
    tree = etree.parse(StringIO(html), parser=parser)

    ff = get_links(tree)
    link = ''
    if len(ff) != 0:
        firstlink = ff[0]
        link = firstlink[8:-3]

    return link

def getImagesPreview(web):
    VIDEO_URL = getLinkPreview(web)
    camera = cv2.VideoCapture(VIDEO_URL)
    if camera.isOpened():
        (grabbed, frame) = camera.read()
        if grabbed:
            name1 = '../static/images/preview.jpg'
            cv2.imwrite(name1, frame)

            connection = pymysql.connect(
                host='localhost',
                user='kommunar',
                password='123',
                db='web_slake',
                charset='utf8mb4',
                cursorclass=DictCursor
            )

            query = "select * from table_region"
            df_region = pd.read_sql(query, connection)

            connection.close()

            Reg = df_region['region'].unique()
            lPoly = []
            for p in Reg:
                lPoly.append(np.array(df_region[df_region['region'] == p][['x', 'y']].values))

            for path in lPoly:
                image =  cv2.polylines(frame, [path], True, (250,240,80), thickness=2)

            name2 = '../static/images/previewWithPolygon.jpg'
            cv2.imwrite(name2, frame)


    return VIDEO_URL

def reset_attempts():
    return 10


def process_video(attempts):

    while(True):
        (grabbed, frame) = camera.read()

        if not grabbed:
            print("disconnected!")
            camera.release()

            if attempts > 0:
                time.sleep(5)
                return True
            else:
                return False

        name1 = './static/images/frame {}.png'.format(time.time())
        cv2.imwrite(name1, frame)



recall = True
attempts = reset_attempts()


if __name__ == "__main__":
    #https: // rtsp.me /embed/aQbSTfEi/
    VIDEO_URL = getImagesPreview('https://rtsp.me/embed/aQbSTfEi/')
    print(VIDEO_URL)
    while (recall):
        camera = cv2.VideoCapture(VIDEO_URL)

        if camera.isOpened():
            print("[INFO] Camera connected at " +
                  datetime.datetime.now().strftime("%m-%d-%Y %I:%M:%S%p"))
            attempts = reset_attempts()
            recall = process_video(attempts)
        else:
            print("Camera not opened " +
                  datetime.datetime.now().strftime("%m-%d-%Y %I:%M:%S%p"))
            camera.release()
            attempts -= 1
            print("attempts: " + str(attempts))
            if attempts<=0:
                break
            # give the camera some time to recover
            time.sleep(5)
            continue