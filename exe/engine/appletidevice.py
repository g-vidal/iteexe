# -*- coding: utf-8 -*-
# ===========================================================================
# eXe 
# Copyright 2004-2005, University of Auckland
# Copyright 2004-2009 eXe Project, http://eXeLearning.org/
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
# ===========================================================================

"""
Java Applet Idevice. Enables you to embed java applet in the browser
"""

try:
    from PIL import Image, ImageDraw
except:
    import Image
    import ImageDraw
from twisted.persisted.styles import requireUpgrade
import logging
import sys

from exe.engine.idevice   import Idevice
from exe.engine.path      import Path, toUnicode
from exe.engine.persist   import Persistable
from exe.engine.resource  import Resource
from exe.engine.translate import lateTranslate

log = logging.getLogger(__name__)

# Constants
GEOGEBRA_FILE_NAMES = set(["geogebra.jar", "geogebra_algos.jar", "geogebra_cas.jar", "geogebra_export.jar", "geogebra_gui.jar", "geogebra_javascript.jar", "geogebra_main.jar", "geogebra_properties.jar", "jlatexmath.jar", "jlm_cyrillic.jar", "jlm_greek.jar"])
JCLIC_FILE_NAMES = set(["jclic.jar"])
SCRATCH_FILE_NAMES = set(["ScratchApplet.jar", "soundbank.gm"])
DESCARTES_FILE_NAMES = set(["Descartes.jar", "Descartes3.jar", "Descartes4.jar", "Descartes4Runtime.jar", "DescartesA.jar", "Descartes_A.jar", "DescartesCalc.jar", "Descartes_R.jar", "Descartes_S.jar", "descinst.jar"])

# Descartes requires scene_num 
SCENE_NUM = 1
# and could need an installed plugin
DESC_PLUGIN = 0
# For Descartes and so:
url = ''
reload(sys)
sys.setdefaultencoding("UTF-8")
# ===========================================================================

class AppletIdevice(Idevice):
    """
    Java Applet Idevice. Enables you to embed java applet in the browser
    """
    persistenceVersion = 1

    def __init__(self, parentNode=None):
        """
        Sets up the idevice title and instructions etc.
        """
        Idevice.__init__(self, 
                         x_(u"Java Applet"), 
                         x_(u"University of Auckland"), 
                         u"",
                         u"",
                         u"",
                             parentNode)
        self.emphasis          = Idevice.NoEmphasis
        self.appletCode        = u""
        self.type              = u"other"
        self._fileInstruc      = x_(u"""Add all the files provided for the applet
except the .txt file one at a time using the add files and upload buttons. The 
files, once loaded will be displayed beneath the Applet code field.""")
        self._codeInstruc      = x_(u""""Find the .txt file (in the applet file) 
and open it. Copy the contents of this file <ctrl A, ctrl C> into the applet 
code field.""")
        self._typeInstruc     = x_(u""" <p>If the applet you're adding was generated 
by one of the programs in this drop down, please select it, 
then add the data/applet file generated by your program. </p>
<p>eg. For Geogebra applets, select geogebra, then add the .ggb file that 
you created in Geogebra.</p>""")
        self.message          = ""
        
    # Properties    
    fileInstruc = lateTranslate('fileInstruc')
    codeInstruc = lateTranslate('codeInstruc')
    typeInstruc = lateTranslate('typeInstruc')

    global DESC_PLUGIN
    DESC_PLUGIN = 0

    def getResourcesField(self, this_resource):
        """
        implement the specific resource finding mechanism for this iDevice:
        """
        # if this_resource is listed within the iDevice's userResources, 
        # then we can assume that this_resource is indeed a valid resource, 
        # even though that has no direct field.
        # As such, merely return the resource itself, to indicate that
        # it DOES belong to this iDevice, but is not a FieldWithResources:
        if this_resource in self.userResources:
            return this_resource

        return None
       
    def getRichTextFields(self):
        """
        Like getResourcesField(), a general helper to allow nodes to search 
        through all of their fields without having to know the specifics of each
        iDevice type.  
        """
        # Applet iDevice has no rich-text fields:
        return []
        
    def burstHTML(self, i):
        """
        takes a BeautifulSoup fragment (i) and bursts its contents to 
        import this idevice from a CommonCartridge export
        """
        # Java Applet Idevice:
        #title = i.find(name='span', attrs={'class' : 'iDeviceTitle' })
        #idevice.title = title.renderContents().decode('utf-8')
        # no title for this idevice.
        # =====> WARNING: not yet loading any of the files!
        # BEWARE also of the appletCode line breaks loading as <br/>,
        # may want change this back to \n or \r\n?
        # AND: also need to load the applet type: Geogebra or Other.
        inner = i.find(name='div', attrs={'class' : 'iDevice emphasis0' })
        self.appletCode= inner.renderContents().decode('utf-8')


    def verifyConn(self, site):
        """
        verify if the URL indicated by the user is reachable
        """    
        import httplib
        import socket
        import re
        timeout = 30
        socket.setdefaulttimeout(timeout)
        try:
            patron = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
            portandhost = re.search(patron, site)
            port = portandhost.group('port')
            host = portandhost.group('host')
            if not portandhost.group('port'):
                port = '80'
            conn = httplib.HTTPConnection(host, port)
            # now the real connection test:
            conn.connect()
        except (httplib.HTTPResponse, socket.error):
            return False
        try:
            # nothing more needed:
            conn.close()
        except:
            pass    
        return True


    def uploadFile(self, filePath):
        """
        Store the upload files in the package
        Needs to be in a package to work.
        """ 
        if self.type == "descartes" and not filePath.endswith(".jar"):
            if filePath.find(",") == -1:
                global SCENE_NUM
                SCENE_NUM = 1
            else:
                SCENE_NUM = int(filePath[:filePath.find(",")])
        if self.type == "descartes" and (filePath.endswith(".htm") or filePath.endswith(".html")):
            global url
            url = filePath
            self.appletCode = self.getAppletcodeDescartes(filePath)
            # none scene was found:
            if self.appletCode == '':
                return None
        else:
            log.debug(u"uploadFile "+unicode(filePath))
            resourceFile = Path(filePath)
            assert self.parentNode, _('file %s has no parentNode') % self.id
            assert self.parentNode.package, \
                    _('iDevice %s has no package') % self.parentNode.id
            if resourceFile.isfile():
                self.message = ""
                Resource(self, resourceFile)
                if self.type == "geogebra":
                    self.appletCode = self.getAppletcodeGeogebra(resourceFile.basename().replace(' ','_'))
                if self.type == "jclic":
                    self.appletCode = self.getAppletcodeJClic(resourceFile.basename().replace(' ','_'))
                if self.type == "scratch":
                    self.appletCode = self.getAppletcodeScratch(resourceFile.basename().replace(' ','_'))
                if self.type == "descartes":
                    self.appletCode = self.getAppletcodeDescartes(resourceFile.basename())
                ## next code should be used to load in the editor the HTML code of the html file:
                # if self.type == "other":
                #     if filePath.endswith(".html") or filePath.endswith(".htm"):
                #         content = open(filePath, 'r')
                #         str = content.read()
                #         self.appletCode = str
                #         content.close()
                #    else:
                #        log.error('File %s is not a HTML file' % resourceFile)
            else:
                log.error('File %s is not a file' % resourceFile)
    
    def deleteFile(self, fileName):
        """
        Delete a selected file
        """
        for resource in self.userResources:
            if resource.storageName == fileName:
                resource.delete()
                break
            
    def getAppletcodeGeogebra(self, filename):
        """
        xhtml string for GeoGebraApplet
        """
        
        html = """
        <applet code="geogebra.GeoGebraApplet.class" archive="geogebra.jar" width="750" height="450">
            <param name="filename" value="%s">
            <param name="framePossible" value="true">
            <param name="java_arguments" value="-Xmx1024m"/>
            <param name="showResetIcon" value="true"/>
            <param name="showAnimationButton" value="true"/>
            <param name="errorDialogsActive" value="true"/>
            <param name="enableRightClick" value="true"/>
            <param name="enableLabelDrags" value="false"/>
            <param name="showMenuBar" value="false"/>
            <param name="showToolBar" value="true"/>
            <param name="showToolBarHelp" value="true"/>
            <param name="enableShiftDragZoom" value="true"/><param name="showAlgebraInput" value="false"/>
            <param name="useBrowserForJS" value="false" />
            <param name="cache_archive" value="geogebra.jar,geogebra_main.jar, geogebra_gui.jar, geogebra_cas.jar,geogebra_algos.jar, geogebra_export.jar, geogebra_javascript.jar,jlatexmath.jar, jlm_greek.jar, jlm_cyrillic.jar,geogebra_properties.jar" />
            Please <a href="http://java.sun.com/getjava"> install Java 1.4</a> (or later) to use this page.
        </applet> """ % filename
        
        return html

    def getAppletcodeJClic(self, filename):
        """
        xhtml string for JClicApplet
        """  
        html = """
            <applet code="JClicApplet" archive="jclic.jar" width="800" height="600">
            <param name="name" value="JClicApplet">
            <param name="activitypack" value="%s">
            <param name="framePossible" value="false">
            Please <a href="http://java.sun.com/getjava"> install Java 1.4</a> (or later) to use this page.
        </applet> """ % filename
        
        return html

    def getAppletcodeScratch(self, project):
        """
        xhtml string for ScratchApplet
        """
        html = """
            <applet id="ProjectApplet" style="display:block" code="ScratchApplet" archive="ScratchApplet.jar" width="482" height="387">
            <param name="project" value="%s">
            <param name="useBrowserForJS" value="false" />
            Please <a href="http://java.sun.com/getjava"> install Java 1.4</a> (or later) to use this page.
        </applet> """ % project
        
        return html


    def downloadFiles(self, stringapplet):
        """
        only for DescartesApplet initially; three jobs:
        1 look for image and macros files in the URL indicated by the user,
        2 modify applet code for a correct exe detection of them after this,
        3 download and store them into the exe project (absolute urls are required).
        Return the code modified.
        """
        from exe.engine.beautifulsoup import BeautifulSoup, BeautifulStoneSoup
        import re
        import urllib
        import urllib2
        import string
        import os
        # import urllib.request
        stringappletmod = stringapplet
        soup = BeautifulSoup(stringapplet)
        
        # ONE: image files:
        key_image = ['archivo=', 'imagem_de_fundo=', 'imagem=', 'imagen=', 'file=', 'fitxer=',
                             'artxibo=', 'image=', 'bg_image=', 'imatge=', 'immagine=', 'irudia=',
                             'irundia=', 'fichier=', 'imaxe=', 'arquivo=', 'immagine_fondo=']
        # paths to the images indicated in the applet code:
        imageslist = []
        for x in key_image:
            if string.find(stringapplet, x) != -1:
                expression = r"%s'([\w\./]+)'" % x
                patron = re.compile(expression)
                for tag in soup.findAll('param'):
                    result = patron.search(tag['value'])
                    if result:
                        if result.group(1) not in imageslist:
                            imageslist.append(result.group(1))
        # modify applet code:
        urlimageslist = []
        for im in imageslist: 
            # put as locals the images' path inside exe editor...
            stringappletmod = stringappletmod.replace(im,im[im.rfind("/")+1:]) 
            # from imageslist, it's neccesary to create the list of absolute paths to the image
            # files because we want to download this images and load them in the project:
            # first quit scene number
            urlnoesc = url[url.find(",")+1:]
            # cut the right side of the last /:
            urlcut = urlnoesc[: urlnoesc.rfind("/")]
            # and extend with the image from the applet code:
            urlimageslist.append(urlcut+"/"+im)
        # repeated no thanks:
        urlimageslist = list(set(urlimageslist))
        # do not forget that it could be image_down and image_over versions
        # of the file in the same place, so... a new extended list:
        urlimgslistextended = []
        for pathimg in urlimageslist:     
            # we trick to urlimageslist adding files that haven't been detected really 
            if pathimg not in urlimgslistextended:
                urlimgslistextended.append(pathimg)
                if string.find(pathimg, '.png') != -1:
                    urlimgslistextended.append(pathimg.replace('.png', '_down.png'))
                    urlimgslistextended.append(pathimg.replace('.png', '_over.png'))
                if string.find(pathimg, '.jpg') != -1:
                    urlimgslistextended.append(pathimg.replace('.jpg', '_down.jpg'))
                    urlimgslistextended.append(pathimg.replace('.jpg', '_over.jpg'))
                if string.find(pathimg, '.gif') != -1:
                    urlimgslistextended.append(pathimg.replace('.gif', '_down.gif')) 
                    urlimgslistextended.append(pathimg.replace('.gif', '_over.gif'))                
        urlimgslistextended = list(set(urlimgslistextended))
        # now we can: download all you can find:
        for pathimgext in urlimgslistextended:
            # the clean name of the image file
            img = pathimgext[pathimgext.rfind("/")+1:]                
            # firstly to test the existence of the file:
            try:
                resp = urllib2.urlopen(pathimgext)
            except urllib2.URLError, e:
                if not hasattr(e, "code"):
                    raise
                resp = e            
            try:
            # download whith its original name:                
                img_down = urllib.urlretrieve(pathimgext, img)
            except:
                print 'Unable to download file'           
            # be sure the file was found:
            if img_down[1].maintype == 'image':
                self.uploadFile(img_down[0])
            os.remove(img_down[0])
        # change the path in the soup, now the file will be local:           
        for x in imageslist:
            if x in soup:
                x = x[x.rfind("/")+1:]     
        
        # TWO: local macros (sometimes a macro that is called may reside inside the jar file)
        # paths to the macros indicated in the applet code:  
        macroslist = []
        key_typo = ['tipo=', 'tipus=', 'type=', 'mota=']
        for x in key_typo:
            if string.find(stringapplet, x) != -1:
                expression = r"%s'ma[ck]ro'" % x
                patron = re.compile(expression)
                for tag in soup.findAll('param'):
                    result = patron.search(tag['value'])
                    if result:
                    # tipo = macro or makro finded, now we need expresion parameter inside value tag                               
                        key_macro = ['expresión=', 'expresion=', 'adierazpen=', 'espressione=', 'expresi&oacute;n=',
                                               'expresi&oacute;=', 'expresi&amp;oacute;n=', 'express&atilde;o=']
                        for y in key_macro:
                            if string.find(tag, y) != -1:
                                # consider sometimes macro file has txt format but sometimes has not format...
                                # and sometimes they are locals and sometimes they are inside the jar file
                                wexpression = ur"%s'(?P<bla>[\w./]+)'" % y # notice unicode conversion
                                wpatron = re.compile(wexpression)
                                # convert tag to unicode string also:
                                utag = unicode(tag)
                                wresult = wpatron.search(utag)
                                if wresult:
                                    macroslist.append(wresult.group('bla'))
        # repeated no thanks:
        macroslist = list(set(macroslist))             
        # from macroslist, it's neccesary to create the list of absolute
        # paths to the macros because we want to download them:
        urlmacroslist=[]
        for mac in macroslist:           
            urlnoesc = url[url.find(",")+1:]
            urlcut = urlnoesc[: urlnoesc.rfind("/")]
            urlmacroslist.append(urlcut+"/"+mac)
            urlmacroslist = list(set(urlmacroslist))
        # we try to download them but really we do not know if they will be
        # physically, as locals -out of the jar file- so our code must look for them, 
        # and if they seem not to be we we will asume they are in the jar file   
        for pathmacro in urlmacroslist:
            macro = pathmacro[pathmacro.rfind("/")+1:]
            try:
                resp = urllib2.urlopen(pathmacro)
            except urllib2.URLError, e:
                if not hasattr(e, "code"):
                    raise
                resp = e              
            if resp.code == 200:
                macro_down = urllib.urlretrieve(pathmacro,macro)         
                self.uploadFile(macro_down[0])
                os.remove(macro_down[0])

                # and modify the applet code inside eXe, now the file will be local:           
                for x in macroslist:
                    if x.endswith('.txt'):
                        if string.find(x,macro) != -1:
                            stringappletmod = stringappletmod.replace(x,macro)
   
        # return soap with images and macros path modified:            
        return stringappletmod
        
    
    def getAppletcodeDescartes(self, filename):
        """
        xhtml string for DescartesApplet
        """
        global SCENE_NUM
        html = ""
        if not filename.endswith(".jar"):
            if filename.endswith(".html") or filename.endswith(".htm"):
                from exe.engine.beautifulsoup import BeautifulSoup, BeautifulStoneSoup   
                import urllib2
                if filename.find(",") == -1:    
                    # firstly verify the URL is reachable, or come back:
                    if self.verifyConn(filename) == False:
                        assert self.parentNode.package, _('Sorry, this URL is unreachable') 
                        return
                    # filename is reachable, go on:                    
                    htmlbytes = urllib2.urlopen(filename)
                else:
                    if self.verifyConn(filename[2:]) == False:
                        return html == ''                   
                    htmlbytes = urllib2.urlopen(filename[2:])
                content = htmlbytes.read()
                # content = content.replace('""','"') Galo swears it won't be necessary
                soup = BeautifulSoup(content)
                i = 0
                appletslist = []
                for ap_old in soup.findAll("applet",{"code":"Descartes.class"}):
                    for resource in reversed(self.userResources):
                        if resource._storageName != ap_old["archive"]:
                            resource.delete()
                    global DESC_PLUGIN
                    DESC_PLUGIN = 0
                    ap_old["codebase"] = "./"
                    appletslist.append(ap_old)   
                for ap_new in soup.findAll("applet",{"code":"descinst.Descartes.class"}):
                    DESC_PLUGIN = 1
                    for resource in reversed(self.userResources):
                        if resource._storageName != 'descinst.jar':
                            resource.delete()
                    ap_new["codebase"] = "./"
                    appletslist.append(ap_new)
                for ap_supernew in soup.findAll("applet",{"code":"descinst.DescartesWeb2_0.class"}):
                    DESC_PLUGIN = 1
                    for resource in reversed(self.userResources):
                        if resource._storageName != 'descinst.jar':
                            resource.delete()
                    ap_supernew["codebase"] = "./"
                    appletslist.append(ap_supernew)
                # TO_DO sometimes applets are included in frame labels (no applets found in the url): 
                # it could begin...:
                # if appletslist == []: # because none <applet> was founded
                #    for ap_frame in soup.findAll("frame src"): # could be problems with that whitespace
                #        DESC_PLUGIN = 1
                #        for resource in reversed(self.userResources):
                #            if resource._storageName != 'descinst.jar':
                #                resource.delete()
                #        if ap_frame["codebase"]:
                #            ap_frame["codebase"] = "./"
                #        appletslist.append(ap_frame)                      
                
                # if none applet was found:
                if appletslist == []:
                    html == ''
                    
                    return html
                
                # finally:                  
                for x in appletslist:
                    u = ''
                    if i == SCENE_NUM -1:
                        u = unicode(x)
                        umod = self.downloadFiles(u)
                        break
                    i = i+1
                htmlbytes.close()
                html = umod
        # now html has the code of the applet for eXe:
        return html
          
    def copyFiles(self):
        """
        if descartes, geogebra, jclic or scratch then copy all jar files, otherwise delete all jar files.
        """
        
        for resource in reversed(self.userResources):
            resource.delete()
            
        self.appletCode = ""
        self.message = ""
        if self.type == "geogebra":
            #from exe.application import application
            from exe import globals
            ideviceDir = globals.application.config.webDir/'templates'            
            for file in GEOGEBRA_FILE_NAMES:
                filename = ideviceDir/file
                self.uploadFile(filename)
            self.appletCode = self.getAppletcodeGeogebra("")
            self.message       = ""
            self._typeInstruc  = x_(u"""Click on the AddFiles button to select the .ggb file and then click on the Upload button.""")
        if self.type == "jclic":
            #from exe.application import application
            from exe import globals
            ideviceDir = globals.application.config.webDir/'templates'            
            for file in JCLIC_FILE_NAMES:
                filename = ideviceDir/file
                self.uploadFile(filename)
            self.appletCode = self.getAppletcodeJClic("")
            self.message       = ""
            self._typeInstruc  = x_(u"""Click on the AddFiles button to select the .jclic.zip file and then click on the Upload button.<p>The activity will be visible when the HTML file will be generated from eXe.""")
        if self.type == "scratch":
            #from exe.application import application
            from exe import globals
            ideviceDir = globals.application.config.webDir/'templates'            
            for file in SCRATCH_FILE_NAMES:
                filename = ideviceDir/file
                self.uploadFile(filename)
            self.appletCode = self.getAppletcodeScratch("")
            self.message       = ""
            self._typeInstruc  = x_(u"""Click on the AddFiles button to select the .sb or .scratch file and then click on the Upload button.""")
        if self.type == "descartes":
            #from exe.application import application
            from exe import globals
            ideviceDir = globals.application.config.webDir/'templates'            
            global DESC_PLUGIN
            for file in DESCARTES_FILE_NAMES:
                filename = ideviceDir/file
                self.uploadFile(filename)
            self.appletCode = self.getAppletcodeDescartes("")
            self.message       = ""
            self._typeInstruc  = x_(u"""Please enter: scene number,URL (no spaces) that include it, eg: 3,http://example.com; click on the Upload button afterwards.""")
        if self.type == "other":
            self._typeInstruc  = x_(u"""Click on the AddFiles button to select the .html or .htm file and then click on the Upload button to get its content.""")




    def upgradeToVersion1(self):
        """
        Called to upgrade to 0.23 release
        """
        self.message       = ""
        self.type == u"other"
        self._typeInstruc  = x_(u""" <p>If the applet you're adding was generated 
by one of the programs in this drop down, please select it, 
then add the data/applet file generated by your program.""")
          
# ===========================================================================
#def register(ideviceStore):
    #"""Register with the ideviceStore"""
    #ideviceStore.extended.append(AppletIdevice())
