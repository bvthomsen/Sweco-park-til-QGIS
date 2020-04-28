# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SwecoPark
                                 A QGIS plugin
 Frontend for SWECO Park Web system
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-11-28
        copyright            : (C) 2019 by Bo Victor Thomsen, AestasGIS 
        email                : bvt@aestas.dk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

def my_form_open(dialog, layer, feature):
    geom = feature.geometry()
    c = dialog.findChild(QWidget, "leTest")
    c.setText('Dummy init')


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SwecoPark class from file SwecoPark.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .sweco_park import SwecoPark
    return SwecoPark(iface)