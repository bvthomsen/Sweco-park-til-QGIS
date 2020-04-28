# -*- coding: utf-8 -*-
from PyQt5.QtCore import QCoreApplication, QSettings, QVariant, Qt,  QDateTime
from PyQt5.QtWidgets import QTreeWidgetItem, QDialog, QLineEdit, QCheckBox, QPushButton, QVBoxLayout
from qgis.utils import iface
from qgis.core  import QgsMessageLog, Qgis, QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsGeometry, QgsLayerTreeGroup, QgsWkbTypes, QgsField, QgsFeatureRequest, QgsExpressionContextUtils, QgsFeature
from json import load, loads, dump, dumps
from inspect import currentframe
from os import path
from base64 import urlsafe_b64encode, urlsafe_b64decode
import requests
#import settings

trClassName= ''
key = 'DumINakkenMetodeSomIkkeFungerer'

def encode(clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return urlsafe_b64encode("".join(enc).encode()).decode()

def decode(enc):
    dec = []
    enc = urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)

def findLayerVariableValue (ename, evalue):

    for layer in QgsProject.instance().layerTreeRoot().findLayers():
        if evalue == QgsExpressionContextUtils.layerScope(layer.layer()).variable(ename): return layer.layer()

    return None

def findLayersVariableValue (ename=None, evalues=None, dbpath=None, dbtnames=None):

    rd = {}
    tot = 0
    fnd = 0

    for ev in evalues:
        tot += 1
        rd[ev]= None
        for l in QgsProject.instance().layerTreeRoot().findLayers():
            if ev == QgsExpressionContextUtils.layerScope(layer.layer()).variable(ename): 
                rd[ev] = layer.layer()
                fnd += 1
                break

    if dbpath is not None: 
        for dbtn in dbtnames:
            rd[dbtn] = None
            tot += 1
            l = QgsVectorLayer("{}|layername={}".format(dbpath,dbtn), dbtn, "ogr")
            if l.isValid():
                rd[dbtn] = l
                fnd += 1
           
    numerr = tot - fnd          
    return numerr, rd

def hLog (mess,tab):

    QgsMessageLog.logMessage(mess,tab, Qgis.Info)


def trInit(message):

    global trClassName
    trClassName = message

# noinspection PyMethodMayBeStatic
def tr(message):

    global trClassName
    return QCoreApplication.translate(trClassName, message)


def hInfo (mess1,mess2,duration=5):

    iface.messageBar().pushMessage (mess1,mess2, Qgis.Info, duration)
    iface.mainWindow().repaint()

def hWarning (mess1,mess2,duration=10):

    iface.messageBar().pushMessage (mess1,mess2, Qgis.Warning, duration)
    iface.mainWindow().repaint()

def hCritical (mess1,mess2,duration=15):

    iface.messageBar().pushMessage (mess1,mess2, Qgis.Critical,duration)
    iface.mainWindow().repaint()

def xStr(s):

    return '' if s is None else str(s)


def addMemoryLayer2tree (type, epsg, name, style, tree, tb):

    epsg = epsg.upper().replace('EPSG:','')

    vl = QgsVectorLayer(wkbtype2str(type)+"?crs=epsg:"+epsg, name , "memory")
    vl.dataProvider().addAttributes([QgsField("id",  QVariant.Int)])
    vl.updateFields()

    if tb:
        n = tree.insertLayer(0,vl)
    else:
        n = tree.addLayer(vl)

    QgsProject.instance().addMapLayer(vl, False)
    hLog(style,currentframe().f_code.co_name)
    vl.loadNamedStyle(style)
    vl.triggerRepaint()

    return vl

def addMemoryLayer2treeNG (name , attr, tree, tb):

    vl = QgsVectorLayer('none', name , "memory")
    vl.dataProvider().addAttributes(attr)
    vl.updateFields()

    if tb:
        n = tree.insertLayer(0,vl)
    else:
        n = tree.addLayer(vl)

    QgsProject.instance().addMapLayer(vl, False)

    return vl

def layerCrs (layer):
    return int (layer.dataProvider().crs().authid()[5:])

def crs2int (crs):
    return int (crs.upper().replace('EPSG:',''))

def removeGroup(groupName):

    # Find conflict group if exists and remove it
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(groupName)
    if group is not None:
        root.removeChildNode(group)

def removeGroupLayer(groupName,layer):

    # Find group if exists

    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(groupName)
    if group is not None:
        # Find layer if exists
        ln = group.findLayer (layer)
        if layer is not None:
            group.removeChildNode(ln)

def clearGroupLayer(groupName,layer):

    # Find group if exists
    root = QgsProject.instance().layerTreeRoot()
    group = root.findGroup(groupName)
    if group is not None:
        ln = group.findLayer (layer)
        if ln is not None:
            ln.layer().dataProvider.truncate()
            return ln

    return None


def cnvobj2obj (gobj,epsg_in,epsg_out):

    if epsg_in == epsg_out:
        return gobj

    else:
        crsSrc = QgsCoordinateReferenceSystem(epsg_in)
        crsDest = QgsCoordinateReferenceSystem(epsg_out)
        xform = QgsCoordinateTransform(crsSrc, crsDest, QgsProject.instance())
        i = gobj.transform(xform)
        return gobj

def cnvobj2wkt (gobj,epsg_in,epsg_out):

    return cnvobj2obj(gobj,epsg_in,epsg_out).asWkt()

def cnvwkt2obj (wkt,epsg_in,epsg_out):

    return cnvobj2obj(QgsGeometry.fromWkt(wkt),epsg_in,epsg_out)

def cnvwkt2wkt (wkt,epsg_in,epsg_out):

    return cnvobj2wkt(QgsGeometry.fromWkt(wkt),epsg_in,epsg_out)

def wkbtype2simple (type):

    my_WkbType = {0:'pnt', 1:'pnt', 2:'lin', 3:'pol', 4:'pnt', 5:'lin', 6:'pol'}
    return my_WkbType[type]

def wkbtype2str (type):

    my_WkbType = {0:'Unknown', 1:'Point', 2:'LineString', 3:'Polygon', 4:'MultiPoint', 5:'MultiLineString', 6:'MultiPolygon', 100:'NoGeometry'}
    return my_WkbType[type]

def fillResultTree (tree, layer, lid, jvar, rc, u1c, u2c):

    # Unfold json
    jDict = loads(jvar)
    res = jDict[rc]
    url1 = jDict[u1c]
    url2 = jDict[u2c]

    # Create parent
    parent = QTreeWidgetItem(tree)
    parent.setText(0,tr(u'{} ({} overlaps)').format(layer.name(),layer.featureCount()))
    parent.setText(1,str(lid))
    parent.setText(2,str(layer.name()))
    parent.setText(3,str(layer.featureCount()))
    parent.setFlags( Qt.ItemIsEnabled| Qt.ItemIsUserCheckable | Qt.ItemIsTristate ) #parent.flags() |
    parent.setCheckState(0, Qt.Checked)

    # Iterate through layer sorted by resColumn ascending
    res = jDict[rc]
    for f in layer.getFeatures(QgsFeatureRequest().addOrderBy(res,True)):

        # Create new item
        child = QTreeWidgetItem(parent)
        child.setText(0,str(f[res]))
        child.setText(1,str(f.id()))
        child.setText(2,str(f[url1]) if url1 != '' else '')
        child.setText(3,str(f[url2]) if url2 != '' else '')
        child.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled| Qt.ItemIsTristate | Qt.ItemIsUserCheckable )
        child.setCheckState(0, Qt.Checked)

def is_http_url(s):
    return re.match('https?://(?:www)?(?:[\w-]{2,255}(?:\.\w{2,6}){1,2})(?:/[\w&%?#-]{1,300})?',s)

def load_qlr_file(self, path):
    # Load qlr into a group owned by us
    try:
        group1 = QgsLayerTreeGroup()
        group2 = QgsProject.instance().layerTreeRoot()
        group = group1

        # On Windows this locks the parent dirs indefinitely
        # See http://hub.qgis.org/issues/14811
        # QgsLayerDefinition.loadLayerDefinition(path, group)

        # Instead handle file ourselves
        f = QFile(path)
        if not f.open(QIODevice.ReadOnly):
            return False
        try:
            doc = QDomDocument()
            if not doc.setContent( f.readAll() ):
                return False

            rc, rs = QgsLayerDefinition.loadLayerDefinition(doc, QgsProject.instance(), group, QgsReadWriteContext())

        finally:
            f.close()

        # Get subtree of nodes
        nodes = group.children()
        # plain list of nodes
        nodeslist = []
        for addedNode in nodes:
            internalid = self._random_string()
            nodeinfo = {'internalid': internalid}
            addedNode.setCustomProperty(QlrManager.customPropertyName, internalid)
            if isinstance(addedNode, QgsLayerTreeGroup):
                nodeinfo['type'] = 'group'
                nodeinfo['name'] = addedNode.name()
            elif isinstance(addedNode, QgsLayerTreeLayer):
                nodeinfo['type'] = 'layer'
                nodeinfo['name'] = addedNode.name()
                nodeinfo['layerid'] = addedNode.layerId()
            nodeslist.append(nodeinfo)
            # Remove from parent node. Otherwise we cant add it to a new parent
            group.takeChild(addedNode)
        self.fileSystemItemToLegendNode[path] = nodeslist

        # Insert them into the main project
        QgsProject.instance().layerTreeRoot().insertChildNodes(0, nodes)
        return True
    except Exception as e:
        self.log('Failed to load qlr at ' + path +': '+ str(e))
        return False


def replaceTxtfile (fname, tsearch, treplace, sname ='.qlr'):
   
    tsearch = tsearch.replace('\\','/')
    treplace = treplace.replace('\\','/')

    # create temp txt file
    import tempfile
    dummy,fopath = tempfile.mkstemp(suffix = sname)  

    fin = open(fname, "rt")
    fout = open(fopath, "wt")  

    for line in fin:
    	fout.write(line.replace(tsearch, treplace))
    	
    fin.close()
    fout.close()

    return fout.name


def read_config(filename):
    file = open(filename)
    dict = load(file)
    file.close()
    return dict

def write_config(filename, config):  # functionality not tested; 2019-11-09
    file = open(filename, mode='w', encoding='utf8')
    dump(config, file, indent=4)
    file.close()
    
class SwecoLogin(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.ticket = ""

        self.leHttpAdr  = QLineEdit(self)
        self.leUserName = QLineEdit(self)
        self.lePassword = QLineEdit(self)

        self.cbAdmData = QCheckBox(self)
        self.cbAdmData.setChecked(False)
        self.cbAdmData.setText('Hent administrative data')

        self.cbCreateLayers = QCheckBox(self)
        self.cbCreateLayers.setChecked(False)
        self.cbCreateLayers.setText('Opret SWECO lagstruktur i projekt')

        self.cbSavePass = QCheckBox(self)
        self.cbSavePass.setChecked(False)
        self.cbSavePass.setText('Sæt username/password som standard')

        self.setWindowTitle("SWECO login")
        self.lePassword.setEchoMode(QLineEdit.Password)

        self.leHttpAdr.setPlaceholderText('Workspace navn')
        self.leUserName.setPlaceholderText('Brugernavn')
        self.lePassword.setPlaceholderText('Kodeord')

        self.buttonLogin = QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)

        layout = QVBoxLayout(self)
        layout.addWidget(self.leHttpAdr)
        layout.addWidget(self.leUserName)
        layout.addWidget(self.lePassword)
        layout.addWidget(self.cbAdmData)
        layout.addWidget(self.cbCreateLayers)
        layout.addWidget(self.cbSavePass)
        layout.addWidget(self.buttonLogin)

    def splitToken (self,token):

        ta = token.split('¤')
        return [ta[0], ta[1],ta[2],int(ta[3]),decode(ta[4]),decode(ta[5]),ta[6],ta[7]]        

    def getTicket (self,token):

        ta = token.split('¤')
        return ta[5]        

    def getReqDetail (self,token):

        ta = token.split('¤')
        return ta[0]+ ta[2]        

    def getReqLogin (self,token):

        ta = token.split('¤')
        return ta[0]+ ta[1]        

    def joinToken (self, reqHttp, reqLogin, reqDetail, seconds, username, password, ticket, time):    
        return '¤'.join([reqHttp, reqLogin, reqDetail ,str(seconds),encode(username),encode(password),ticket,time])

    def refreshLogin(self,token):

        tn = QDateTime.currentDateTime()
        p = self.splitToken (token)

        self.leHttpAdr.setText(p[0])
        self.reqLogin = p[1]
        self.reqDetail = p[2]
        self.timeout = p[3]
        self.leUserName.setText(p[4])
        self.lePassword.setText(p[5])
        self.ticket = p[6] 
        self.timeToken = p[7] 
        self.timeNow = tn.toString(Qt.ISODate)

        show = (self.timeToken == '')
        self.lastResult =  QDialog.Accepted
        
        if not show:

            tt = QDateTime().fromString(self.timeToken,Qt.ISODate) 
            show = (tt.secsTo(tn) >= self.timeout) 

        if show: self.lastResult = self.exec_()

        return self.ticket, self.joinToken (self.leHttpAdr.text(),self.reqLogin, self.reqDetail, self.timeout, self.leUserName.text(), self.lePassword.text(), self.ticket, self.timeToken) 

    def handleLogin(self):

        reqCom = self.leHttpAdr.text() + self.reqLogin
        scode, rdict = handleRequest (False,reqCom.format(self.leUserName.text(),self.lePassword.text()), None, currentframe().f_code.co_name)   
        if scode == 200:
    
            if rdict['code'] == '0':
                self.ticket = rdict['value']['ticket']
                self.timeToken = self.timeNow
                hLog('Login time  : {}'.format(self.timeToken),'sweco')
                hLog('Login ticket: {}'.format(self.ticket),'sweco')
                self.accept()
            else:
                hCritical ('SWECO Park rest-api','Login to SWECO: Bad user or password',10)
        else:
            hCritical ('SWECO Park rest-api','Login HTTP response code = ' + str (scode),10)

def handleRequest (isPost,url,package=None,name=''):

    loglayer = QgsVectorLayer (QgsExpressionContextUtils.projectScope(QgsProject.instance()).variable('sweco_log'),'blah','ogr')
    stime = QDateTime.currentDateTime().toString(Qt.ISODate) 
    
    if isPost:
        r = requests.post(url,json=package) if package else requests.post(url)
    else:
        r = requests.get(url) 

    scode = r.status_code
    dict = r.json() if r.status_code == 200 else None

    if loglayer.isValid():
        feat = QgsFeature(loglayer.fields())
        feat['operation'] = 'post' if isPost else 'get'
        feat['url'] = url
        feat['package'] = dumps(package, indent=2) if package else ''
        feat['status_code'] = str(scode)
        feat['dict'] = dumps(dict, indent=2) if dict else ''
        feat['timestamp'] = stime 
        feat['module'] = name  
        loglayer.dataProvider().addFeatures ([feat])

    return scode, dict  

