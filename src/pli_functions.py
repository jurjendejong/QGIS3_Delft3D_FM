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

            x = float(ls[0])
            y = float(ls[1])
            z = ' '.join(ls[2:]).replace("'", "")

            fet = QgsFeature()
            fet.setGeometry(QgsPoint(x, y))
            fet.setAttributes([z])
            pr.addFeatures([fet])

    return vl


def load_tekal(filepath):
    _, filename = os.path.split(filepath)
    layername, extension = os.path.splitext(filename)

    d = tek.tekal(filepath)  # initialize
    d.info(filepath)  # get file meta-data: all blocks

    vl = QgsVectorLayer("LineString", layername, "memory")
    pr = vl.dataProvider()

    attribute = "name"

    # add fields
    pr.addAttributes([QgsField(attribute, QVariant.String)])
    vl.updateFields()  # tell the vector layer to fetch changes from the provider

    for ii in range(len(d.blocks)):
        d_name = d.blocks[ii].name
        d_data = d.read(ii)
        pli = []
        for ix in range(len(d_data[0])):
            pli.append(QgsPoint(d_data[0][ix], d_data[1][ix]))

        # If line of just one points: duplicate
        if len(d_data[0]) == 1:
            pli.append(QgsPoint(d_data[0][0] + 0.01, d_data[1][0] + 0.01))

        # add a feature
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPolyline(pli))

        fet.setAttributes([d_name])
        pr.addFeatures([fet])

    return vl


def save_point(layer, filename):
    output_file = open(filename, 'w')
    for f in layer.getFeatures():
        geom_point = f.geometry().asPoint()
        line = '{:.3f},{:.3f},'.format(geom_point.x(), geom_point.y()) + ','.join(f.attributes()) + '\n'
        output_file.write(line)
    output_file.close()


def save_polyline(layer, filename):
    output_file = open(filename, 'w')
    for iFeature, f in enumerate(layer.getFeatures()):
        geom_line = f.geometry().asPolyline()
        if len(f.attributes()) > 0 and f.attributes()[0]:
            feature_name = str(f.attributes()[0]).replace(' ', '_')
        else:
            feature_name = 'Feature_{}'.format(iFeature)
        output_file.write(feature_name + '\n')
        output_file.write('{} {}\n'.format(len(geom_line), 2))  # Space as seperater in Deltashell
        for g in geom_line:
            output_file.write('{:.3f} {:.3f}\n'.format(g.x(), g.y()))
    output_file.close()


def save_polygon(layer, filename):
    output_file = open(filename, 'w')
    feature_id = 0
    for feature in layer.getFeatures():
        fpol = feature.geometry().asPolygon()
        for geomLine in fpol:
            output_file.write('Feature{}\n'.format(feature_id))
            output_file.write('{},{}\n'.format(len(geomLine), 2))
            for g in geomLine:
                output_file.write('{:.3f},{:.3f}\n'.format(g.x(), g.y()))
            feature_id += 1
    output_file.close()


def save_multipolygon(layer, filename):
    print('Processing to ldb (multi polygon)')
    output_file = open(filename, 'w')
    feature_id = 0
    for feature in layer.getFeatures():
        fpols = feature.geometry().asMultiPolygon()
        for fpol in fpols:
            for geomLine in fpol:
                output_file.write('Feature{}\n'.format(feature_id))
                output_file.write('{},{}\n'.format(len(geomLine), 2))
                for g in geomLine:
                    output_file.write('{:.3f},{:.3f}\n'.format(g.x(), g.y()))
                feature_id += 1
    output_file.close()
