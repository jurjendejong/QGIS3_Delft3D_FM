# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Delft3D_FlexibleMesh
                                 A QGIS plugin
 This plugin will provide basic tools for Flexible Mesh
version=0.1 
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-10-10
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Jurjen de Jong, Deltares
        email                : jurjen.dejong@deltares.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox

from qgis.core import Qgis, QgsVectorLayer, QgsFeature, QgsProject, QgsField, QgsGeometry, QgsPoint, \
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsWkbTypes
from qgis.PyQt.QtCore import QVariant

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Delft3D_FlexibleMesh_dialog import Delft3D_FlexibleMeshDialog
from .src import pli_functions as dfm_pli

import os.path


class Delft3D_FlexibleMesh:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Delft3D_FlexibleMesh_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Delft3D Flexible Mesh')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.directory = None

        self.toolbar = self.iface.addToolBar(u'Delft3D_FlexibleMesh')
        self.toolbar.setObjectName(u'Delft3D_FlexibleMesh')

        self.dlg = Delft3D_FlexibleMeshDialog()
        self.dlg.path_savefile.clear()
        self.dlg.pushButton.clicked.connect(self._select_save_path)


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Delft3D_FlexibleMesh', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # icon_path = ':/plugins/Delft3D_FlexibleMesh/icon.png'
        # self.add_action(
        # icon_path,
        # text=self.tr(u'Delft3D FM Toolbox'),
        # callback=self.run,
        # parent=self.iface.mainWindow())

        icon_path = ':/plugins/Delft3D_FlexibleMesh/icons/save.png'
        self.add_action(
            icon_path,
            text='Save to .pli/.pol/.xyz',
            callback=self.save_pli,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/Delft3D_FlexibleMesh/icons/incoming.png'
        self.add_action(
            icon_path,
            text='Open .pli/.pol/.xyz',
            callback=self.open_pli,
            parent=self.iface.mainWindow())

    def _select_save_path(self):
        # Get path of layer in combobox
        selected_layer_index = self.dlg.comboBox.currentIndex()
        layers = self.iface.mapCanvas().layers()
        selected_layer_path = layers[selected_layer_index].source()
        if os.path.isfile(selected_layer_path):
            selected_layer_filename, ext = os.path.splitext(selected_layer_path)
            suggested_path = selected_layer_filename + '.ldb'
        else:
            suggested_path = self.directory

        # Open and process dialog
        filename, _ = QFileDialog.getSaveFileName(self.dlg, "Select output file ",
                                                  suggested_path)
        self.dlg.path_savefile.setText(filename)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Delft3D Flexible Mesh'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def open_pli(self):
        filepath, _ = QFileDialog.getOpenFileName(None, "Select pli-file ", self.directory,
                                                  '*')  # .ldb,*.pol,*.pli,*.xyn,*.xyz')
        if not os.path.isfile(filepath): return

        self.iface.messageBar().pushMessage("Open pli: <b>{}</b>.".format(filepath), Qgis.Info)
        self.directory, filename = os.path.split(filepath)
        _, extension = os.path.splitext(filename)

        if extension == '.xyz' or extension == '.xyn':
            vl = dfm_pli.load_xyz(filepath)
        else:
            vl = dfm_pli.load_tekal(filepath)

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        QgsProject.instance().addMapLayer(vl)
        vl.updateExtents()

        # Enable labels
        if not extension == 'name':
            label_settings = QgsPalLayerSettings()
            # label.readFromLayer(vl)
            # label.enabled = True
            label_settings.fieldName = 'name'
            # label.writeToLayer(vl)
            label = QgsVectorLayerSimpleLabeling(label_settings)

            vl.setLabeling(label)
            vl.setLabelsEnabled(True)
        vl.updateExtents()
        self.iface.mapCanvas().setExtent(vl.extent())

        # vl.triggerRepaint()

    def save_pli(self):
        """Run method that performs all the real work"""
        layers = self.iface.mapCanvas().layers()

        layer_list = []
        for layer in layers:
            layer_list.append(layer.name())
        self.dlg.comboBox.clear()
        self.dlg.comboBox.addItems(layer_list)

        selected_layer = layer_list.index(self.iface.activeLayer().name())
        self.dlg.comboBox.setCurrentIndex(selected_layer)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if not result:
            return

        filename = self.dlg.path_savefile.text()

        selected_layer_index = self.dlg.comboBox.currentIndex()
        selected_layer = layers[selected_layer_index]

        if selected_layer.wkbType() == QgsWkbTypes.Point:
            self.iface.messageBar().pushMessage('Saving layer to xyz', Qgis.Info)
            dfm_pli.save_point(selected_layer, filename)

        elif (selected_layer.wkbType() == QgsWkbTypes.LineString) or (
                selected_layer.wkbType() == QgsWkbTypes.LineString25D):
            self.iface.messageBar().pushMessage('Saving layer to pli (polyline)', Qgis.Info)
            dfm_pli.save_polyline(selected_layer, filename)

        elif selected_layer.wkbType() == QgsWkbTypes.Polygon:
            self.iface.messageBar().pushMessage('Saving layer to pol (polygon)', Qgis.Info)
            dfm_pli.save_polygon(selected_layer, filename)

        elif selected_layer.wkbType() == QgsWkbTypes.MultiLineString:
            # self.iface.messageBar().pushMessage('Not yet implemented', Qgis.Warning)
            
            self.iface.messageBar().pushMessage('Saving layer to pli (MultiLineString)', Qgis.Info)
            dfm_pli.save_multipolyline(selected_layer, filename)

        elif selected_layer.wkbType() == QgsWkbTypes.MultiPolygon:
            self.iface.messageBar().pushMessage('Saving layer to pol (multipolygon)', Qgis.Info)
            dfm_pli.save_multipolygon(selected_layer, filename)

        else:
            self.iface.messageBar().pushMessage('Layer type not recognised. wkbType: ' + str(selected_layer.wkbType()),
                                                level=Qgis.Critical)

        self.iface.messageBar().pushMessage('Saving finished', Qgis.Info)
