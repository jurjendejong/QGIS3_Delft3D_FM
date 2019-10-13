from qgis.core import QgsVectorLayer, QgsFeature, QgsProject, QgsField, QgsGeometry, QgsPoint
from qgis.PyQt.QtCore import QVariant
import os.path
from . import tekal as tek


def load_xyz(filepath):
    _, filename = os.path.split(filepath)
    layername, extension = os.path.splitext(filename)

    vl = QgsVectorLayer("Point", layername, "memory")
    pr = vl.dataProvider()

    # add fields
    if extension == 'xyz':
        attribute = 'z'
    else:
        attribute = 'name'

    pr.addAttributes([QgsField(attribute, QVariant.String)])
    vl.updateFields()  # tell the vector layer to fetch changes from the provider

    with open(filepath) as f:
        for line in f:
            ls = line.strip().split()

            X = float(ls[0])
            Y = float(ls[1])
            Z = ' '.join(ls[2:]).replace("'", "")

            fet = QgsFeature()
            fet.setGeometry(QgsPoint(X, Y))
            fet.setAttributes([Z])
            pr.addFeatures([fet])

    return vl


def load_tekal(filepath):
    _, filename = os.path.split(filepath)
    layername, extension = os.path.splitext(filename)

    D = tek.tekal(filepath)  # initialize
    D.info(filepath)  # get file meta-data: all blocks

    vl = QgsVectorLayer("LineString", layername, "memory")
    pr = vl.dataProvider()

    attribute = "name"

    # add fields
    pr.addAttributes([QgsField(attribute, QVariant.String)])
    vl.updateFields()  # tell the vector layer to fetch changes from the provider

    for ii in range(len(D.blocks)):
        name = D.blocks[ii].name
        M = D.read(ii)
        P = []
        for ix in range(len(M[0])):
            P.append(QgsPoint(M[0][ix], M[1][ix]))

        # If line of just one points: duplicate
        if len(M[0]) == 1:
            P.append(QgsPoint(M[0][0] + 0.01, M[1][0] + 0.01))

        # add a feature
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPolyline(P))

        fet.setAttributes([name])
        pr.addFeatures([fet])

    return vl


def save_point(layer, filename):
    output_file = open(filename, 'w')
    for f in layer.getFeatures():
        geomPoint = f.geometry().asPoint()
        line = '{:.3f},{:.3f},'.format(geomPoint.x(), geomPoint.y()) + ','.join(f.attributes()) + '\n'
        output_file.write(line)
    output_file.close()


def save_polyline(layer, filename):
    output_file = open(filename, 'w')
    for iFeature, f in enumerate(layer.getFeatures()):
        geomLine = f.geometry().asPolyline()
        if len(f.attributes()) > 0 and f.attributes()[0]:
            featureName = str(f.attributes()[0]).replace(' ', '_')
        else:
            featureName = 'Feature_{}'.format(iFeature)
        output_file.write(featureName + '\n')
        output_file.write('{} {}\n'.format(len(geomLine), 2))  # Space as seperater in Deltashell
        for g in geomLine:
            output_file.write('{:.3f} {:.3f}\n'.format(g.x(), g.y()))
    output_file.close()


def save_polygon(layer, filename):
    output_file = open(filename, 'w')
    fId = 0
    for feature in layer.getFeatures():
        fpol = feature.geometry().asPolygon()
        for geomLine in fpol:
            output_file.write('Feature{}\n'.format(fId))
            output_file.write('{},{}\n'.format(len(geomLine), 2))
            for g in geomLine:
                output_file.write('{:.3f},{:.3f}\n'.format(g.x(), g.y()))
            fId += 1
    output_file.close()


def save_multipolygon(layer, filename):
    print('Processing to ldb (multi polygon)')
    output_file = open(filename, 'w')
    fId = 0
    for feature in layer.getFeatures():
        fpols = feature.geometry().asMultiPolygon()
        for fpol in fpols:
            for geomLine in fpol:
                output_file.write('Feature{}\n'.format(fId))
                output_file.write('{},{}\n'.format(len(geomLine), 2))
                for g in geomLine:
                    output_file.write('{:.3f},{:.3f}\n'.format(g.x(), g.y()))
                fId += 1
    output_file.close()
