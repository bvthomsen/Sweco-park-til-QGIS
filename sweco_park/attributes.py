# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget,QTreeWidgetItem,QAbstractItemView,QMessageBox, QTableWidgetItem
from qgis.core import QgsProject, QgsExpressionContextUtils, QgsFeatureRequest
from qgis.PyQt.QtCore import Qt, QDateTime
import uuid 
from sweco_park.helper import hLog, hInfo, hWarning, hCritical, findLayerVariableValue, SwecoLogin, handleRequest
#, tr , removeGroup, clearGroupLayer, addMemoryLayer2tree, addMemoryLayer2treeNG, cnvobj2wkt, wkbtype2simple, cnvobj2obj, fillResultTree, removeGroupLayer
import requests
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
#import settings -- brug SwecoPark.settings
from inspect import currentframe

gbDialog = None
gbLayer = None
gbTree = None
gbTest = None
gbEtId = None
gbId = None
gbEtKey = None
gbEtName = None
gbName = None
gbType = None
gbLogin = None
gbUuid = None
gbTwAttributter = None

def my_form_open(dialog, layer, feature):

    global gbDialog
    gbDialog = dialog

    global gbLayer
    gbLayer = layer

    global gbTree
    if not gbTree: 
        gbTree = dialog.findChild(QWidget,"twElementTyper")
        gbTree.setSelectionMode(QAbstractItemView.SingleSelection)
        gbTree.itemDoubleClicked.connect(gbTreeItemDoubleClicked)

    gbGetAttributeDataLocal = dialog.findChild(QWidget,"pbGetAttributeDataLocal")
    gbGetAttributeDataLocal.clicked.connect(gbGetAttributeDataLocalClicked)

    gbGetAttributeDataSweco = dialog.findChild(QWidget,"pbGetAttributeDataSweco")
    gbGetAttributeDataSweco.clicked.connect(gbGetAttributeDataSwecoClicked)

    gbGetAttributeDataDefault = dialog.findChild(QWidget,"pbGetAttributeDataDefault")
    gbGetAttributeDataDefault.clicked.connect(gbGetAttributeDataDefaultClicked)

    global gbUuid
    if not gbUuid: 
        gbUuid = dialog.findChild(QWidget,"pbUuid")
        gbUuid.clicked.connect(pbUuidClicked)

    global gbTest
    if not gbTest: gbTest = dialog.findChild(QWidget,"leTest")

    global gbId
    if not gbId: gbId = dialog.findChild(QWidget,"id")

    global gbEtId
    if not gbEtId: gbEtId = dialog.findChild(QWidget,"et_id")

    global gbEtKey
    if not gbEtKey: gbEtKey = dialog.findChild(QWidget,"et_key")

    global gbEtName
    if not gbEtName: gbEtName = dialog.findChild(QWidget,"et_name")

    global gbName
    if not gbName: gbName = dialog.findChild(QWidget,"name")

    global gbType
    if not gbType: gbType = layer.geometryType()

    global gbLogin
    if not gbLogin: gbLogin = SwecoLogin(None)

    j = ['Point','Line','Polygon']
    gType = j[layer.geometryType()]

    eLayer = findLayerVariableValue('sweco_function','etypes_layer')

    twElementtyperLoadData(gbTree, eLayer, gType)

    global gbTwAttributter
    if not gbTwAttributter: gbTwAttributter = dialog.findChild(QWidget,"twAttributter")


    buttonBox = dialog.findChild(QWidget,"buttonBox")

    # Disconnect the signal that QGIS has wired up for the dialog to the button box.
    #buttonBox.accepted.disconnect(gbDialog.accept)
 
    # Wire up our own signals.
    buttonBox.accepted.connect(validate)
    #buttonBox.rejected.connect(myDialog.reject)
 
 
def validate():

    tbl = gbTwAttributter
    if tbl.rowCount() > 0:
    
        edLayer = findLayerVariableValue('sweco_function','element_detail_layer')
        if edLayer is None:
            hCritical ('SWECO Update Element details','Table with element details not found',10)
    
        else:
    
            s = "delete from element_attributes where elementid = '{}'"   
            gpkg_path = edLayer.dataProvider().dataSourceUri().split('|')
            db = QSqlDatabase.addDatabase("QSPATIALITE")
            db.setDatabaseName(gpkg_path[0])
            if db.open():
        
                query = QSqlQuery()
                sqlTxt = s.format(gbId.text())
                hLog(sqlTxt,"sweco")  
                query.exec_(sqlTxt) 
                db.close()
    
        pr = edLayer.dataProvider()
    
        feats = []
        for i in range(tbl.rowCount()):
            f = QgsFeature(edLayer.fields())
            for j in range (1,22): 
                f.setAttribute(j, tbl.item(i,j).text())
            feats.append(f)

        pr.addFeatures(feats)

    
def twElementtyperLoadData (tree,layer,gtype):
    
    # Clear existing tree & set column width
    tree.clear()
    tree.setColumnWidth(0, 110)
    tree.setColumnWidth(1, 4)
    tree.setColumnWidth(2, 100)
    tree.setColumnWidth(3, 0)
    tree.setColumnWidth(4, 0)
    tree.setColumnWidth(5, 0)

    # Iterate through layer sorted by parentid ascending
    for f in layer.getFeatures(QgsFeatureRequest().addOrderBy('parentid',True, True)):

        if f['geometrytype'] == gtype or f['parentid'] == '':    

            parent = None
        
            # Is parentid blank ?
            if f['parentid'] == '':
        
                # Yes, set parent to tree
                parent = tree
        
            else:
        
                # No, find parent in tree
                clist = tree.findItems(f['parentid'], Qt.MatchExactly|Qt.MatchRecursive, 3);
                for c in clist: parent = c
        
            # Append row to parent
            if parent is not None: 
                child = QTreeWidgetItem(parent)
                child.setText(0, f['key'])
                child.setText(1, '0' if f['geometrytype'] == 'Point' else '1' if f['geometrytype'] == 'Line' else '2')
                child.setText(2, f['name'])
                child.setText(3, f['id'])
                child.setText(4, f['parentid'])
                child.setText(5, str(f['allowec']))

    root = tree.invisibleRootItem()
    child_count = root.childCount()
    for i in range(child_count-1, -1, -1):
        item = root.child(i)
        if item.childCount() == 0 and (item.text(5) == 'False' or int(item.text(1))!= gbType) : root.removeChild(item) 

    tree.setSortingEnabled(True)
    tree.sortByColumn(0,0) 
    tree.hideColumn(1)
    tree.hideColumn(3)
    tree.hideColumn(4)
    tree.hideColumn(5)
   
def gbTreeItemDoubleClicked(item, column_no):
    
    if item.text(5)=='True' and int(item.text(1))==gbType:
        gbEtId.setText(item.text(3))
        gbEtKey.setText(item.text(0))
        gbEtName.setText(item.text(2)) 
        prefix = item.text(0)+'-'
        filter = "name LIKE '{}%'".format(prefix)
        gbTest.setText(filter)

        suffix = '00000'
        for f in gbLayer.getFeatures(QgsFeatureRequest().setFilterExpression(filter).addOrderBy('name',False, False).setLimit(1)):
            suffix = f['name']
        suffix = suffix.replace (prefix,'')
        pos = suffix.find('-') 
        if pos > -1: suffix = suffix[:pos] 
        suffix = "{:05d}".format(int(suffix)+1)
        
        gbName.setText(prefix+suffix) 
           
def pbUuidClicked():

    buttonReply = QMessageBox.question(None, "Generering af nyt UUID !!", "Bruges *kun* efter copy/paste af objekter i kortvindue. Vil du virkelig give posten et nyt UUID ?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if buttonReply == QMessageBox.Yes:
        gbId.setText(str(uuid.uuid1()))

def gbGetAttributeDataLocalClicked ():

    tview = gbTwAttributter
    etid = gbEtId.text()
    id = gbId.text()
    edLayer = findLayerVariableValue('sweco_function','element_detail_layer')

    if edLayer is None:
        hCritical ('SWECO Update Element details','Table with element details not found',10)

    elif etid != '' and id != '':

        loadTwAttributter (edLayer, tview, id, gbType, etid,0)

    else:
        hCritical ('SWECO Update Element details','Not possible to show/import/generate element atrributtes, because id and/or element type is vot set',10)    
    
def gbGetAttributeDataSwecoClicked ():

    tview = gbTwAttributter
    etid = gbEtId.text()
    id = gbId.text()
    edLayer = findLayerVariableValue('sweco_function','element_detail_layer')

    if edLayer is None:
        hCritical ('SWECO Update Element details','Table with element details not found',10)

    elif etid != '' and id != '':

        loadTwAttributter (edLayer, tview, id, gbType, etid,1)

    else:
        hCritical ('SWECO Update Element details','Not possible to show/import/generate element atrributtes, because id and/or element type is vot set',10)    

def gbGetAttributeDataDefaultClicked ():

    tview = gbTwAttributter
    etid = gbEtId.text()
    id = gbId.text()
    edLayer = findLayerVariableValue('sweco_function','element_detail_layer')

    if edLayer is None:
        hCritical ('SWECO Update Element details','Table with element details not found',10)

    elif etid != '' and id != '':

        loadTwAttributter (edLayer, tview, id, gbType, etid,2)

    else:
        hCritical ('SWECO Update Element details','Not possible to show/import/generate element atrributtes, because id and/or element type is vot set',10)    


def loadTwAttributter (edLayer, tview, id, gtype, etid, atype):

    tview.clear()
    for i in range(22): tview.setColumnWidth(i,0)
    tview.setColumnWidth(4, 150)
    tview.setColumnWidth(11,175)
    tview.setHorizontalHeaderLabels(['fid','elementid','id','key','name','description','unit','datatype','mandatory','readonly','defaultvalue','value','validationmin','validationmax','validationdecimal','validationexpression','validationsqlexpression','validationerrmessage','elementattributetypeid','validationvalues','children','parent'])

    if atype == 0:

        # Find attribute date in local table
        feats = getElementDetailData(edLayer, id)
        if feats:
            hInfo ('SWECO Update Element details','Data found in local table',5)
        else:
            hWarning ('SWECO Update Element details','Data could not be found in local table',4)

    elif atype == 1:
    
        # Find attribute date in SWECO and put into local table
        elementDetailUpdateData(edLayer, id)
        feats = getElementDetailData(edLayer, id)

        if feats: 
            hInfo ('SWECO Update Element details','Data generated using SWECO api',5)
        else:
            hWarning ('SWECO Update Element details','Data could not be found at SWECO',4)

    else: # atype == 2

        # Generate attribute data from another element and put into local table
        elementDetailGenerateData(edLayer, id, gtype, etid)
        feats = getElementDetailData(edLayer, id)
        if feats: 
            hInfo ('SWECO Update Element details','Data generated using defalt values',5)
        else:
            hWarning ('SWECO Update Element details','Data could not be generated, no template in local table',4)

    tview.setRowCount(len(feats))
    for i,f in enumerate(feats):
        for j,item in enumerate(f):
            tview.setItem(i,j, QTableWidgetItem(str(item)))
    

def getElementDetailData(edLayer, id):

    feats = []

    for f in edLayer.getFeatures(QgsFeatureRequest().setFilterExpression("elementid = '{}'".format(id))):
        feats.append(f)

    return feats


def elementDetailUpdateData(edLayer, id):

    pr = edLayer.dataProvider()
    gpkg_path = pr.dataSourceUri().split('|')

    attLayerRef = QgsVectorLayer("{}|{}_ref".format(gpkg_path[0],gpkg_path[1]), "Element attributes reference layer", "ogr")

    if not attLayerRef.isValid(): 
        hCritical ('SWECO Import data','Table with element attribute references not found',10)
    else:

        pr2 = attLayerRef.dataProvider()

        # Check token and maybe show login dialog
        ticket, token = gbLogin.refreshLogin(QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('sweco_start'))
        QgsExpressionContextUtils.setProjectVariable(QgsProject.instance(),'sweco_start', token)
    
        tNow = QDateTime.currentDateTime() 
    
        # Get dict with elementtyper
        httpadr = gbLogin.getReqDetail(token)
##
        scode, dict = handleRequest (False,httpadr.format(id,ticket),None,currentframe().f_code.co_name)   
        if scode == 200:


#        response = requests.get(httpadr.format(id,ticket))
#        hLog(httpadr.format(id,ticket),"sweco")   
#         
#        
#        hLog(gpkg_path[0],"sweco")  
#    
#        if response.status_code == 200:
#      
#            dict = response.json()
            if "ElementAttributes" in dict:

                hLog(str(dict),"sweco")   
                feats = []
                
                for d in dict['ElementAttributes']:
                
                    f = QgsFeature(edLayer.fields())
                    f.setAttribute('elementid', id or '')
                    f.setAttribute('id', d["Id"] or '')
                    f.setAttribute('key', d["Key"] or '')
                    f.setAttribute('name', d["Name"] or '')
                    f.setAttribute('description', d["Description"] or '')
                    f.setAttribute('unit', d["Unit"] or '')
                    f.setAttribute('datatype', d["DataType"] or '')
                    f.setAttribute('mandatory', d["Mandatory"] or '')
                    f.setAttribute('readonly', d["ReadOnly"] or '')
                    f.setAttribute('defaultvalue', d["DefaultValue"] or '')
                    f.setAttribute('value', d["Value"] or '')
                    f.setAttribute('validationmin', d["ValidationMin"] or '')
                    f.setAttribute('validationmax', d["ValidationMax"] or '')
                    f.setAttribute('validationdecimal', d["ValidationDecimal"] or '')
                    f.setAttribute('validationexpression', d["ValidationExpression"] or '')
                    f.setAttribute('validationsqlexpression', d["ValidationSqlExpression"] or '')
                    f.setAttribute('validationerrmessage', d["ValidationErrMessage"] or '')
                    f.setAttribute('elementattributetypeid', d["ElementAttributeTypeId"] or '')
                    f.setAttribute('validationvalues', d["ValidationValues"] or '')
                    f.setAttribute('children', d["Children"] or '')
                    f.setAttribute('parent', d["Parent"] or '')
                    feats.append(f)
        
                pr.addFeatures(feats)
                pr2.addFeatures(feats)
            else:                    
                hCritical ('SWECO Park rest-api','SWECO not responding as expected, no data fetched',10)

def elementDetailGenerateData(edLayer, id, gtype, etid):

    hLog("Start Generatedata: id: '{}' gtype {} rtid: '{}' ".format(id, gtype, etid),"sweco")  
    
    s = """ 
    insert into element_attributes (
      elementid,
      id,
      key,
      name,
      description,
      unit,
      datatype,
      mandatory,
      readonly,
      defaultvalue,
      value,
      validationmin,
      validationmax,
      validationdecimal,
      validationexpression,
      validationsqlexpression,
      validationerrmessage,
      elementattributetypeid,
      validationvalues,
      children,
      parent
    )
      select  
        \'{}\' as elementid,
        CreateUUID() as id,
        key,
        name,
        description,
        unit,
        datatype,
        mandatory,
        readonly,
        defaultvalue,
        defaultvalue as value,
        validationmin,
        validationmax,
        validationdecimal,
        validationexpression,
        validationsqlexpression,
        validationerrmessage,
        elementattributetypeid,
        validationvalues,
        children,
        parent
      from element_attributes where elementid in (
        select a.elementid from element_attributes a join {} b on (a.elementid = b.id) 
        where b.et_id = \'{}\' group by a.elementid order by count(*) desc limit 1)
    
    """  
    
    gpkg_path = edLayer.dataProvider().dataSourceUri().split('|')
    
    hLog(gpkg_path[0],"sweco")  
    db = QSqlDatabase.addDatabase("QSPATIALITE")
    db.setDatabaseName(gpkg_path[0])
    
    if db.open():
    
        query = QSqlQuery()
        ttype = 'pnt' if gtype == 0 else 'lin' if gtype == 1 else 'pol' 
        tname = 'elements_{}'.format(ttype)
        sqlTxt = s.format(id,tname,etid)
        hLog(sqlTxt,"sweco")  
        query.exec_(sqlTxt) 
        db.close()
