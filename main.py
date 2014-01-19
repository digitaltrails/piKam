# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# piKam main.py 
#
# Copyright (C) 2013: Michael Hamilton
# The code is GPL 3.0(GNU General Public License) ( http://www.gnu.org/copyleft/gpl.html )
#
from kivy.support import install_twisted_reactor
install_twisted_reactor()
from twisted.internet import reactor, protocol, task
from twisted.protocols import basic

from kivy.app import App
from kivy.app import Widget
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.core.image import ImageData
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

import Image as PyImage
import cPickle
import os
import inspect
import StringIO

from piKamCommon import PiKamRequest
from piKamCommon import SCENE_OPTIONS,AWB_OPTIONS,METERING_OPTIONS,IMXFX_OPTIONS,COLFX_OPTIONS,ISO_OPTIONS,ENCODING_OPTIONS


SETTINGS_JSON_DATA = """[
    { "type":    "title",
      "title":   "PiKam Server" },
    { "type":    "string",
      "title":   "Server Name",
      "desc":    "Hostname or IP address of a PiKamServer",
      "section": "Server",
      "key":     "hostname" },
    { "type":    "numeric",
      "title":   "Server Port",
      "desc":    "Host post on PiKamServer",
      "section": "Server",
      "key":     "port" },
    { "type":    "title",
      "title":   "PiKam Camera" },             
    { "type":    "numeric",
      "title":   "Sharpness",
      "desc":    "Image sharpness -100..100",
      "section": "Camera",
      "key":     "sharpness" },
    { "type":    "numeric",
      "title":   "Jpeg Quality",
      "desc":    "Jpeg Quality 0..100 Auto=0",
      "section": "Camera",
      "key":     "quality" },
    { "type":    "options",
      "title":   "Encoding",
      "desc":    "Image encoding",
      "options": %s,
      "section": "Camera",
      "key":     "encoding" },
    {
      "type":    "bool",
      "title":   "Horz Flip",
      "desc":    "Flip image horizontally.",
      "section": "Camera",
      "key":     "hflip"},          
    {
      "type":    "bool",
      "title":   "Vert Flip",
      "desc":    "Flip image vertically.",
      "section": "Camera",
      "key":     "vflip" },
      
    { "type":    "title",
      "title":   "Misc" },   
          
    {
      "type":    "bool",
      "title":   "Image Carousel",
      "desc":    "Display images in a swipe left/right carousel.",
      "section": "Misc",
      "key":     "carousel" },
      
    { "type":    "numeric",
      "title":   "Carousel Size",
      "desc":    "Carousel maximum images (2..n)",
      "section": "Misc",
      "key":     "numSlides" },
      
    {
      "type":    "bool",
      "title":   "Live Preview",
      "desc":    "Display semi-live preview.",
      "section": "Misc",
      "key":     "preview" },
      
    { "type":    "numeric",
      "title":   "Live Preview Quality",
      "desc":    "Jpeg Quality 0..100 Auto=0",
      "section": "Misc",
      "key":     "previewQuality" },   

    { "type":    "numeric",
      "title":   "Live Preview Refresh",
      "desc":    "Seconds between updates - fraction",
      "section": "Misc",
      "key":     "previewRefresh" },   
      
    {
      "type":    "bool",
      "title":   "Horizontal Layout",
      "desc":    "Layout controls horizontally.",
      "section": "Misc",
      "key":     "horizontalLayout" },
    {
      "type":    "bool",
      "title":   "Spash Image",
      "desc":    "Display a splash image on startup.",
      "section": "Misc",
      "key":     "splash" }
]
""" % str(ENCODING_OPTIONS).replace("'", '"')

#print SETTINGS_JSON_DATA

def textureFromPyImage(pyImg):
    raw = pyImg.tostring()
    width, height = pyImg.size
    print width, height
    imdata = ImageData(width, height, 'rgb', raw)
    texture = Texture.create_from_data(imdata)
    texture.flip_vertical()
    return texture
    
def pyImageFromStr(str):
    return PyImage.open(StringIO.StringIO(str))

class PiKamModel(PiKamRequest):
    isoOptions = ISO_OPTIONS
    awbOptions = AWB_OPTIONS
    sceneOptions = SCENE_OPTIONS
    meteringOptions = METERING_OPTIONS
    imfxOptions = IMXFX_OPTIONS
    colfxOptions = COLFX_OPTIONS
      
    def setConfig(self, config):
        if config.get('Camera', 'encoding'):
            self.encoding = config.get('Camera', 'encoding')
        if config.get('Camera', 'sharpness') != '0':
            self.sharpness = config.get('Camera', 'sharpness')
        if config.get('Camera', 'quality') != '0':
            self.quality = config.get('Camera', 'quality')
        if config.get('Camera', 'hflip') != '0':
            self.hflip = None
        if config.get('Camera', 'vflip') != '0':
            self.vflip = None
            
    def toRequest(self):
        request = PiKamRequest()
        for n, v in inspect.getmembers(self):
            if hasattr(request, n):
                setattr(request, n, v)
        return request

# Declare both screens
class PiKamHorizontalScreen(Screen):
    pass

class PiKamVerticalScreen(Screen):
    pass

class PiKamWidget(Widget):
    pass

class PiKamClient(basic.NetstringReceiver):
    
    # Max message/jpeg length we are prepared to handle
    MAX_LENGTH = 100000000   
    
    def connectionMade(self):
        self.factory.app.on_connection(self.transport)
        
    def dataReceived(self, data):
        self.factory.app.displayProgress(len(data))
        return basic.NetstringReceiver.dataReceived(self, data)

    def stringReceived(self, data):
        self.factory.app.processRemoteResponse(data)
        
class PiKamClientFactory(protocol.ClientFactory):
    protocol = PiKamClient
    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        self.app.displayError("connection lost")
        self.app.chdkConnection = None

    def clientConnectionFailed(self, conn, reason):
        self.app.displayError("connection failed")
        self.app.chdkConnection = None
        
        
class PiKamApp(App):
    chdkConnection = None
    model = PiKamModel()
    ndFilter = False
    exposureComp = 0 # TODO
    previewImage = None
    waitingForImage = False
    previewTask  = None    
    screenMgr = None
    directCamera = None
   
    def build(self):
        self.screenMgr = ScreenManager()
        horzScreen = PiKamHorizontalScreen(name='horz')
        vertScreen = PiKamVerticalScreen(name='vert')    
        x,y = Window.system_size
        detectedLandscape = x > y and False # Not working on Android - darn!
        for screenWidget in ( horzScreen, vertScreen ) if (detectedLandscape or self.config.get('Misc', 'horizontalLayout') == '1') else ( vertScreen, horzScreen ):
            self.screenMgr.add_widget(screenWidget) 
 
        if self.config.get('Misc', 'splash') != '0' and os.path.exists('piKamSplash.jpg'):
            with open ('piKamSplash.jpg', "r") as splashFile:
                data = splashFile.read()
            self.displayImage(data)
        self.reconnect()
        print vars(self)
        #Window.rotation = Window.rotation + 90
        Window.on_rotate(self.rotate)
        return self.screenMgr
    
    def rotate(self, screenName=None):
        print "rotate"
        if self.screenMgr.current == 'horz':
            self.screenMgr.current = 'vert'
        else:
            self.screenMgr.current = 'horz'
        #Window.rotation = Window.rotation + 90
    
    def build_config(self, config):
        config.setdefaults('Server', {'hostname': '', 'port': '8000'}) 
        config.setdefaults('Camera', {'encoding': 'jpg', 'quality': 0, 'sharpness': 0, 'hflip': 0, 'vflip': 0})
        config.setdefaults('Misc',   {'carousel': 1, 'splash': 1, 'preview': 1, 'horizontalLayout':1, 'numSlides': 10, 'previewQuality':5, 'previewRefresh':1.5})
        
    def build_settings(self, settings):
        # Javascript Object Notation
        settings.add_json_panel('PiKam App', self.config, data=SETTINGS_JSON_DATA)
            
    def on_config_change(self, config, section, key, value):
        if config is self.config:
            if section == 'Server':
                self.reconnect()
            if key == 'preview' or key == 'previewQuality' or key == 'previewRefresh':
                self.disablePreview()
                self.enablePreview()
            if key == 'horizontalLayout':
                self.screenMgr.current = 'horz' if self.config.get('Misc', 'horizontalLayout') != '0' else 'vert'
                # Force image to be regenerated and reparented in new widget hierarchy
                self.previewImage = None
                
    def displayInfo(self, message, title='Info'):
        popContent = BoxLayout(orientation='vertical')
        popContent.add_widget(Label(text=message))
        popup = Popup(title=title,
                    content=popContent,
                    text_size=(len(message), None),
                    size_hint=(.8, .33))
        popContent.add_widget(Button(text='Close', size_hint=(1,.33), on_press=popup.dismiss))
        popup.open()

    def currentTop(self):
        return self.screenMgr.current_screen

    def displayError(self, message, title='Error'):
        self.displayInfo(message, title)
        
    def displayProgress(self, value):
        self.currentTop().downloadProgress.value += value
        
    def displayBusyWaiting(self, dt=None):
        if dt == None:
            #print "schedule"
            self.busyWaiting = True
            Clock.schedule_interval(self.displayBusyWaiting, 1 / 10.)
            return
        # Fake progress updates until the real updates happen
        
        if self.busyWaiting:
            self.currentTop().downloadProgress.value += 10000
            return True
        else:
            # If the values differ, then 
            #print "stop"
            return False
    
    def stopBusyWaiting(self):
        self.busyWaiting = False
    
         
    def displayImage(self, data):
        self.displayBusyWaiting()
        try:
            useCarousel = self.config.get('Misc', 'carousel') != '0'
            # On some droids kivy cannot load large images - so downsize for display
            pyImg = PyImage.open(StringIO.StringIO(data))
            # Convert to "thumbnail" display size in place.
            pyImg.thumbnail((1024,1024), PyImage.ANTIALIAS)
            # Load Kivy Image from PyImage without going to disk
            image = Image(texture=textureFromPyImage(pyImg))
            if useCarousel:
                self.currentTop().imageCarousel.add_widget(image)
                # Set the carousel to display the new image (could exhaust memory - perhaps only display last N)
                self.currentTop().imageCarousel.index = len(self.currentTop().imageCarousel.slides) - 1
                numSlides = int(self.config.get('Misc', 'numSlides'))
                if len(self.currentTop().imageCarousel.slides) > numSlides:
                    self.currentTop().imageCarousel.remove_widget(self.currentTop().imageCarousel.slides[0])
            else:
                self.currentTop().imageLayout.clear_widgets()
                self.currentTop().imageLayout.add_widget(image)
                
        finally:
            self.stopBusyWaiting()

    def displayPreview(self, data):
        useCarousel = self.config.get('Misc', 'carousel') != '0'
        if self.previewImage:
            #print 'update preview'
            self.previewImage.texture = textureFromPyImage(pyImageFromStr(data))
            if useCarousel:
                # Shuffle to end
                oldIndex = self.currentTop().imageCarousel.index
                self.currentTop().imageCarousel.remove_widget(self.previewImage)
                self.currentTop().imageCarousel.add_widget(self.previewImage)
                if oldIndex == len(self.currentTop().imageCarousel.slides) - 1:
                    self.currentTop().imageCarousel.index = len(self.currentTop().imageCarousel.slides) - 1
        else:
            #print 'initial preview'
            self.previewImage =  Image(texture=textureFromPyImage(pyImageFromStr(data)),mipmap=True)
            self.previewImage.nocache = True
            if useCarousel:
                oldIndex = self.currentTop().imageCarousel.index
                self.currentTop().imageCarousel.add_widget(self.previewImage)
                # Set the carousel to display the new image (could exhaust memory - perhaps only display last N)
                if oldIndex == len(self.currentTop().imageCarousel.slides) - 1:
                    self.currentTop().imageCarousel.index = len(self.currentTop().imageCarousel.slides) - 1
            else:
                self.currentTop().imageLayout.clear_widgets()
                self.currentTop().imageLayout.add_widget(self.previewImage)

    def on_connection(self, connection):
        self.displayInfo('Connected succesfully!')
        self.chdkConnection = connection  
        self.prepareCamera()
        self.enablePreview()
        
    def on_start(self):
        if self.config.get('Server', 'hostname') == '':
            # On a Raspberry Pi - start preview - if remote it
            # will be started by on_connection
            self.enablePreview()

    def on_pause(self):
        #reactor._mainLoopShutdown()
        self.disablePreview()
        return True

    def on_resume(self):
        self.reconnect()
        return True
   
    def sendRemoteCommand(self, message):
        if self.chdkConnection:
            # Compose Netstring format message and send it (might be able to call sendString but is undocumented)
            self.chdkConnection.write(str(len(message)) + ':' + message + ',')
        else:
            self.displayError('No connection to server')
            
    def processRemoteResponse(self, message):
        try:
            self.stopBusyWaiting()
            # Turn the response string back nto a dictionary and see what it is
            result = cPickle.loads(message)
            if result['type'] == 'image':
                self.displayImage(result['data'])
                # Save the image and add an internal copy to the GUI carousel.
                filename = result['name']
                with open(filename, 'wb') as imageFile:
                    imageFile.write(result['data'])
            elif result['type'] == 'preview':
                self.displayPreview(result['data'])
            elif result['type'] == 'error':
                self.displayError(result['message'])
            else:
                self.displayError('Unexpected kind of message.')
            self.currentTop().downloadProgress.value = 0
        finally:
            self.waitingForImage = False

    def takeSnapshot(self, preview = False):
        self.waitingForImage = True
        self.model.setConfig(self.config)
        command = {}
        command['cmd'] = 'shoot'
        args = self.model.toRequest()
        if preview:
            args.height = 480
            args.width = 640
            args.encoding = 'jpg'
            args.quality = self.config.get('Misc', 'previewQuality')
            args.replyMessageType = 'preview'
            
        if self.config.get('Server', 'hostname') == '':
            # On a Raspberry Pi already
            self.directSnapshot(args, preview)
            self.waitingForImage = False
        else:
            command['args'] = args
            # Turn the request into a string so it can be sent in Netstring format
            self.sendRemoteCommand(cPickle.dumps(command))
            if not preview:
                self.displayBusyWaiting()
        
    def prepareCamera(self):
        command = {'cmd': 'prepareCamera'}
        args = self.model.toRequest()
        command['args'] = args
        self.sendRemoteCommand(cPickle.dumps(command))
        pass
        
    def reconnect(self):
        hostname = self.config.get('Server', 'hostname')
        if hostname == '':
            return
        port = self.config.getint('Server', 'port')
        reactor.connectTCP(hostname, port, PiKamClientFactory(self))
    
    def requestPreview(self):
        #print 'pv'
        if self.waitingForImage:
            print 'already waiting'
            return
        useCarousel = self.config.get('Misc', 'carousel') != '0'
        numSlides = len(self.currentTop().imageCarousel.slides)
        if useCarousel and numSlides != 0 and self.currentTop().imageCarousel.index != numSlides - 1:
            # Not looking at preview - don't refresh it
            return
        self.takeSnapshot(preview=True)

    def enablePreview(self):
        if self.config.get('Misc', 'preview') == '0' or self.previewTask:
            return
        print 'enablePreview'
        self.waitingForImage = False
        self.previewTask = task.LoopingCall(self.requestPreview)
        refresh = float(self.config.get('Misc', 'previewRefresh'))
        self.previewTask.start(refresh) 
        
    def directSnapshot(self, parameters, preview):
        # running on a Raspberry Pi
        if self.directCamera == None:
            try:
                print "Using picam directly"
                from piKamPicamServer import PiKamPicamServerProtocal
                self.directCamera = PiKamPicamServerProtocal()
            except:
                print "Using raspistill directly"
                from piKamServer import PiKamServerProtocal
                self.directCamera = PiKamServerProtocal()
        try:
            imageFilename, imageBinary, replyMessageType = self.directCamera.takePhoto(parameters)
            if preview:
                self.displayPreview(imageBinary)
            else:
                self.displayImage(imageBinary)   
        except:
            self.displayError('Error on attemping direct photo.\nNo remote hostname set, you need to be running this on a Raspberry Pi.')
            
    def disablePreview(self):
        if self.previewTask: 
            print 'disablePreview'
            self.previewTask.stop()
            self.previewTask = None
        self.waitingForImage = False
        
if __name__ == '__main__':
    PiKamApp().run()
