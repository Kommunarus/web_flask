import cv2
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.path as mpltPath
import matplotlib.patches as patches

from sklearn.utils.linear_assignment_ import linear_assignment
#from scipy.optimize import linear_sum_assignment as linear_assignment


from VDT.detector import CarDetector
from VDT.tracker import Tracker
from VDT.helpers import draw_box_label, countGate, box_iou2

import pymysql
from pymysql.cursors import DictCursor



detector = CarDetector()



# Global variables to be used by funcitons of VideoFileClop
frame_count = 0 # frame counter

max_age = 4  # no.of consecutive unmatched detection before 
             # a track is deleted

min_hits =1  # no. of consecutive matches needed to establish a track

tracker_list =[] # list for trackers
# list for track ID
track_id_list= 0

debug = False

count_gate = [0,0,0,0]

def assign_detections_to_trackers(trackers, detections, iou_thrd = 0.1):
    '''
    From current list of trackers and new detections, output matched detections,
    unmatchted trackers, unmatched detections.
    '''

    IOU_mat= np.zeros((len(trackers),len(detections)),dtype=np.float32)
    for t,trk in enumerate(trackers):
        #trk = convert_to_cv2bbox(trk) 
        for d,det in enumerate(detections):
         #   det = convert_to_cv2bbox(det)
            IOU_mat[t,d] = box_iou2(trk,det)

    # Produces matches
    # Solve the maximizing the sum of IOU assignment problem using the
    # Hungarian algorithm (also known as Munkres algorithm)

    matched_idx = linear_assignment(-IOU_mat)

    unmatched_trackers, unmatched_detections = [], []
    for t,trk in enumerate(trackers):
        if(t not in matched_idx[:,0]):
            unmatched_trackers.append(t)

    for d, det in enumerate(detections):
        if(d not in matched_idx[:,1]):
            unmatched_detections.append(d)

    matches = []

    # For creating trackers we consider any detection with an 
    # overlap less than iou_thrd to signifiy the existence of 
    # an untracked object

    for m in matched_idx:
        if(IOU_mat[m[0],m[1]]<iou_thrd):
            unmatched_trackers.append(m[0])
            unmatched_detections.append(m[1])
        else:
            matches.append(m.reshape(1,2))

    if(len(matches)==0):
        matches = np.empty((0,2),dtype=int)
    else:
        matches = np.concatenate(matches,axis=0)

    return matches, np.array(unmatched_detections), np.array(unmatched_trackers)


def pipeline(img, connection):
    '''
    Pipeline function for detection and tracking
    '''
    global frame_count
    global tracker_list
    global max_age
    global min_hits
    global track_id_list
    global debug
    global count_gate

    frame_count+=1

    img_dim = (img.shape[1], img.shape[0])
    z_box = detector.get_localization(img) # measurement
    if debug:
       print('Frame:', frame_count)

    x_box =[]
    if debug:
        for i in range(len(z_box)):
           img1= draw_box_label(img, z_box[i], box_color=(255, 0, 0))
           plt.imshow(img1)
        plt.show()

    if len(tracker_list) > 0:
        for trk in tracker_list:
            x_box.append(trk.box)


    matched, unmatched_dets, unmatched_trks \
    = assign_detections_to_trackers(x_box, z_box, iou_thrd = 0.1)
    if debug:
         print('Detection: ', z_box)
         print('x_box: ', x_box)
         print('matched:', matched)
         print('unmatched_det:', unmatched_dets)
         print('unmatched_trks:', unmatched_trks)


    # Deal with matched detections     
    if matched.size >0:
        for trk_idx, det_idx in matched:
            z = z_box[det_idx]
            z = np.expand_dims(z, axis=0).T
            tmp_trk= tracker_list[trk_idx]
            tmp_trk.kalman_filter(z)
            xx = tmp_trk.x_state.T[0].tolist()
            xx =[xx[0], xx[2], xx[4], xx[6]]
            x_box[trk_idx] = xx
            tmp_trk.box =xx
            tmp_trk.hits += 1
            tmp_trk.no_losses = 0

    # Deal with unmatched detections      
    if len(unmatched_dets)>0:
        for idx in unmatched_dets:
            z = z_box[idx]
            z = np.expand_dims(z, axis=0).T
            tmp_trk = Tracker() # Create a new tracker
            x = np.array([[z[0], 0, z[1], 0, z[2], 0, z[3], 0]]).T
            tmp_trk.x_state = x
            tmp_trk.predict_only()
            xx = tmp_trk.x_state
            xx = xx.T[0].tolist()
            xx =[xx[0], xx[2], xx[4], xx[6]]
            tmp_trk.box = xx
            track_id_list += 1
            tmp_trk.id = track_id_list# assign an ID for the tracker
            tracker_list.append(tmp_trk)
            x_box.append(xx)

    # Deal with unmatched tracks       
    if len(unmatched_trks)>0:
        for trk_idx in unmatched_trks:
            tmp_trk = tracker_list[trk_idx]
            tmp_trk.no_losses += 1
            tmp_trk.predict_only()
            xx = tmp_trk.x_state
            xx = xx.T[0].tolist()
            xx =[xx[0], xx[2], xx[4], xx[6]]
            tmp_trk.box =xx
            x_box[trk_idx] = xx


    # The list of tracks to be annotated  
    good_tracker_list =[]
    for trk in tracker_list:
        if ((trk.hits >= min_hits) and (trk.no_losses <=max_age)):
             good_tracker_list.append(trk)
             x_cv2 = trk.box
             if debug:
                 print('updated box: ', x_cv2)
                 print()

             box_color = (255, 220, 100)

             img= draw_box_label(img, x_cv2, box_color = box_color, id=trk.id) # Draw the bounding boxes on the images
             left, top, right, bottom = x_cv2[1], x_cv2[0], x_cv2[3], x_cv2[2]
             x_mid = (right + left) / 2
             y_mid = (bottom + top) / 2
             query = "INSERT INTO web_slake.coordinate(frame, id, x, y) " \
                     "VALUES(%s,%s,%s,%s)"
             args = (frame_count, trk.id, x_mid, y_mid)
             cursor = connection.cursor()
             cursor.execute(query, args)
             connection.commit()


             #if trk.counted == False:
             #   img= countGate(img, x_cv2, frame_count, trk, count_gate)
    # Book keeping
    deleted_tracks = filter(lambda x: x.no_losses >max_age, tracker_list)

    #for trk in deleted_tracks:
            #track_id_list.append(trk.id)

    tracker_list = [x for x in tracker_list if x.no_losses<=max_age]

    if debug:
       print('Ending tracker_list: ',len(tracker_list))
       print('Ending good tracker_list: ',len(good_tracker_list))


    return img


def plotline(image, lPoly):

    '''   font = cv2.FONT_HERSHEY_SIMPLEX
    font_size = 1.5
    font_color = (51, 200, 250)

    cv2.putText(image, str(count_gate[0]), (127, 325), font, font_size, font_color, 1, cv2.LINE_AA)
    cv2.putText(image, str(count_gate[1]), (362, 392), font, font_size, font_color, 1, cv2.LINE_AA)
    cv2.putText(image, str(count_gate[2]), (598, 460), font, font_size, font_color, 1, cv2.LINE_AA)
    cv2.putText(image, str(count_gate[3]), (904, 548), font, font_size, font_color, 1, cv2.LINE_AA)

    image = cv2.line(image, (0,290), (1277,660), (255, 255, 255), 3)
    '''
    for path in lPoly:
        image =  cv2.polylines(image, [path], True, (250,120,80), thickness=2)

    return image

def startODaTr(pathIn, pathOut, countFrame):

    connection = pymysql.connect(
            host='localhost',
            user='kommunar',
            password='123',
            db='web_slake',
            charset='utf8mb4',
            cursorclass=DictCursor
        )

    query = "DELETE FROM web_slake.coordinate"
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()

    query = "select * from table_region"
    df_region = pd.read_sql(query, connection)

    Reg = df_region['region'].unique()
    lPoly = []
    for p in Reg:
        lPoly.append(np.array(df_region[df_region['region'] == p][['x', 'y']].values))

    print(pathIn)
    readAllFile = False
    imagesOld = []

    while not readAllFile:
        images = os.listdir(pathIn)

        if len(imagesOld) != 0:
            imagesNew = list(set(images)-set(imagesOld))
        else:
            imagesNew = images

        print('imagesNew {}'.format(len(imagesNew)))

        imagesi = [plt.imread(pathIn+file) for file in sorted(imagesNew, key=lambda fname: int(fname.split('.')[0]))]

        for i in range(len(imagesi)):
            image = imagesi[i]
            image_box = pipeline(image, connection)
            image_box = plotline(image_box, lPoly)
            cv2.imwrite(pathOut + str(i + len(imagesOld)) +'.jpg', image_box)

        imagesOld = images
        if len(images) >= countFrame:
            readAllFile = True

    connection.close()


if __name__ == "__main__":

    connection = pymysql.connect(
            host='localhost',
            user='kommunar',
            password='123',
            db='web_slake',
            charset='utf8mb4',
            cursorclass=DictCursor
        )

    startODaTr('../static/images/cam/', '../static/images/processing/', connection)



