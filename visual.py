import base64
from random import random
import pymysql
from pymysql.cursors import DictCursor
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mpltPath
from matplotlib import cm
from io import BytesIO
import shapely
from shapely.geometry import LineString, Point
from matplotlib.patches import Circle, Wedge, Polygon


plt.rcParams.update({'figure.max_open_warning': 0})

def plotGraf(totalObject, partObject, timePartObject, freqFrame, lineObject, mapTrajectory):

    connection = pymysql.connect(
        host='localhost',
        user='kommunar',
        password='123',
        db='web_slake',
        charset='utf8mb4',
        cursorclass=DictCursor
    )

    query = "select * from coordinate"
    df_coordinate = pd.read_sql(query, connection)

    query = "select * from table_region"
    df_region = pd.read_sql(query, connection)

    connection.close()


    numberPlot = totalObject+partObject+timePartObject+lineObject+mapTrajectory

    if numberPlot == 0:
        return ''
    if numberPlot == 1 or numberPlot == 2 or numberPlot == 3:
        nrows=1
        ncols=numberPlot
        figsize = (20, 7)
    if numberPlot == 4 or numberPlot == 5:
        nrows=2
        ncols=3
        figsize = (20, 14)

    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize = figsize)

    if totalObject:

        if nrows == 1:
            ax_loc = ax[0]
        else:
            ax_loc = ax[0,0]

        df_totalObject = df_coordinate.groupby(['frame'])['id'].count()

        df_totalObject.plot(ax=ax_loc)
        ax_loc.grid(zorder=0)
        ax_loc.set_title('Количество объектов в кадре')
        ax_loc.set_xlabel('Кадр')
        ax_loc.set_ylabel('Количество машнн')

    if partObject or timePartObject:
        Reg= df_region['region'].unique()
        lPoly_3 = []
        col_3 = []
        for p in Reg:
            dots = df_region[df_region['region'] == p][['x', 'y']].values
            if dots.shape[0] > 2:
                lPoly_3.append(mpltPath.Path(dots))
                col_3.append(str(p))

        if len(lPoly_3) > 0:
            df_area_3 = np.zeros((len(df_coordinate), len(col_3)))

            for index_in, (_, row) in enumerate(df_coordinate.iterrows()):
                for ind, poly in enumerate(lPoly_3):
                    inside = poly.contains_points([[row['x'], row['y']]])

                    if inside[0]:
                        df_area_3[index_in,ind] = 1

    if partObject:

        if totalObject:
            if nrows == 1:
                ax_loc = ax[1]
            else:
                ax_loc = ax[0,1]
        else:
            if nrows == 1:
                ax_loc = ax[0]
            else:
                ax_loc = ax[0,0]

        df_partObject = df_coordinate.join(pd.DataFrame(df_area_3, columns=col_3))
        df_part = df_partObject.groupby(['frame'])[col_3].sum()
        df_part.plot.area(ax=ax_loc,stacked=False, colormap='winter')
        ax_loc.grid(zorder=0)
        ax_loc.set_title('Количество объектов в замкнутых областях')
        ax_loc.set_xlabel('Кадр')
        ax_loc.set_ylabel('Количество машин')

    if timePartObject:

        pred = totalObject + partObject
        if nrows == 1:
                ax_loc = ax[pred]
        else:
                ax_loc = ax[0,pred]

        df_partObject = df_coordinate.join(pd.DataFrame(df_area_3, columns=col_3))
        df_part = df_partObject.groupby(['id'])[col_3].sum()
        df_part3 = df_part[col_3] / freqFrame
        df_part3[df_part[col_3] > 0].plot.box(ax=ax_loc)
        ax_loc.grid(zorder=0)
        ax_loc.set_title('Время нахождения объектов в замкнутых областях')
        ax_loc.set_xlabel('Замкнутая область, №')
        ax_loc.set_ylabel('Время (сек)')




    if lineObject:

        pred = totalObject + partObject + timePartObject
        if pred == 0 or pred == 1 or pred == 2:
            if nrows == 1:
                    ax_loc = ax[pred]
            else:
                    ax_loc = ax[0,pred]
        elif pred == 3:
                    ax_loc = ax[1,0]


        Reg= df_region['region'].unique()
        lPoly_2 = []
        col_2 = []
        for p in Reg:
            dots = df_region[df_region['region'] == p][['x', 'y']].values
            if dots.shape[0] == 2:
                lPoly_2.append(dots)
                col_2.append(str(p))

        if len(lPoly_2) > 0:
            lid = df_coordinate['id'].unique()

            df_part = pd.DataFrame(columns=['id', 'gate', 'cross'])

            for id in lid:
                dots = df_coordinate[df_coordinate['id'] == id][['x', 'y']].values
                if dots.shape[0] > 1:
                    line1 = LineString(dots)
                    for ind, poly in enumerate(lPoly_2):
                        line2 = LineString(poly)
                        if line1.crosses(line2):
                            df_part = df_part.append({'id': id, 'gate': col_2[ind], 'cross': 1}, ignore_index=True)
                        else:
                            df_part = df_part.append({'id': id, 'gate': col_2[ind], 'cross': 0}, ignore_index=True)
                            #df_area_2[index, ind] = 1

            df_part = df_part.groupby('gate')['cross'].sum()
            df_part.plot.bar(ax=ax_loc, x = 'gate', y = 'cross')

        ax_loc.set_title('Количество пересечений с линиями (области с двумя точками)')
        ax_loc.set_xlabel('Лииия, №')
        ax_loc.set_ylabel('Количество')

    if mapTrajectory:

        pred = totalObject + partObject + timePartObject+lineObject
        if pred == 0 or pred == 1 or pred == 2:
            if nrows == 1:
                    ax_loc = ax[pred]
            else:
                    ax_loc = ax[0,pred]
        elif pred == 3:
                    ax_loc = ax[1,0]
        elif pred == 4:
                    ax_loc = ax[1,1]

        ax_loc.set_title('Карта траекторий')
        ax_loc.set_xlabel('x')
        ax_loc.set_ylabel('y')

        pred2 = totalObject + partObject + timePartObject + lineObject + mapTrajectory
        if pred2 == 0 or pred2 == 1 or pred2 == 2:
            if nrows == 1:
                ax_loc2 = ax[pred]
            else:
                ax_loc2 = ax[0, pred]
        elif pred2 == 3:
            ax_loc2 = ax[1, 0]
        elif pred2 == 4:
            ax_loc2 = ax[1, 1]
        elif pred2 == 5:
            ax_loc2 = ax[1, 2]

        ax_loc2.grid(zorder=0)
        ax_loc2.set_title('Покадровое появление объектов')
        ax_loc2.set_xlabel('Кадр')
        ax_loc2.set_ylabel('Номер объекта')

        #plt.gca().set_aspect('equal', adjustable='box')
        colors = {}
        for index_in, (_, row) in enumerate(df_coordinate.iterrows()):
            color = colors.setdefault(row['id'], (random(), random(), random()))
            ax_loc.scatter(row['x'], row['y'], color = color)
            ax_loc2.scatter(row['frame'], row['id'], color=color)

        Reg= df_region['region'].unique()
        lPoly = []
        for p in Reg:
            dots = df_region[df_region['region'] == p][['x', 'y']].values
            if dots.shape[0] > 1:
                poly = plt.Polygon(dots, ec="k", alpha = 0.2)
                ax_loc.add_patch(poly)
        ax_loc.invert_yaxis()



    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    buffer = b''.join(buf)
    b2 = base64.b64encode(buffer)
    fig2 = b2.decode('utf-8')

    #plt.show()

    plt.cla()
    plt.close(fig)

    return fig2


if __name__ == "__main__":

    plotGraf(1,True, 1, 5, 1, 1)
