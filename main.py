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
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from kivy.app import App
from kivy.app import Widget
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

import Image as PyImage
import cPickle
import os

SCENE_OPTIONS = "off,auto,night,nightpreview,backlight,spotlight,sports,snow,beach,verylong,fixedfps,antishake,fireworks".split(',')
AWB_OPTIONS = "off,auto,sun,cloud,shade,tungsten,fluorescent,incandescent,flash,horizon".split(',')
METERING_OPTIONS = "average,spot,backlit,matrix".split(',')
IMXFX_OPTIONS = "none,negative,solarise,sketch,denoise,emboss,oilpaint,hatch,gpen,pastel,watercolour,film,blur,saturation,colourswap,washedout,posterise,colourpoint,colourbalance,cartoon".split(',')
COLFX_OPTIONS = "none,U,V".split(',')
ISO_OPTIONS = "auto,50,100,200,400,800".split(",")
ENCODING_OPTIONS = "jpg,bmp,gif,png".split(",")

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
      
    {
      "type":    "bool",
      "title":   "Spash Image",
      "desc":    "Display a splash image on startup.",
      "section": "Misc",
      "key":     "splash" }
]
""" % str(ENCODING_OPTIONS).replace("'", '"')

#print SETTINGS_JSON_DATA

class PiKamModel():
 
    isoOptions = ISO_OPTIONS
    awbOptions = AWB_OPTIONS
    sceneOptions = SCENE_OPTIONS
    meteringOptions = METERING_OPTIONS
    imfxOptions = IMXFX_OPTIONS
    colfxOptions = COLFX_OPTIONS
    
    zoomTimes = 1
    ev = 0
    brightness = 50
    contrast = 0
    saturation = 0

    iso = 'auto'
    awb = 'auto'
    metering = 'average'
    scene = 'off'
    imxfx = 'none'
    colfx = 'none'
    
    def toMap(self, config):
        map = { 
            '--ISO': self.iso, 
            '--ev': self.ev, 
            '--brightness': self.brightness, 
            '--contrast': self.contrast, 
            '--saturation': self.saturation, 
            '--awb': self.awb,
            '--metering': self.metering,
            '-t':0,
            }
        if self.zoomTimes > 1.0:
            roi = ",".join([str(v*(1.0/self.zoomTimes)) for v in (1.0,1.0,1.0,1.0)])
            map["--roi"] = roi
        if self.imxfx != 'none':
            map['--imxfx'] = self.imxfx
        if self.colfx != 'none':
            map['--colfx'] = self.colfx
        if self.scene != 'off':
            map['--exposure'] = self.scene
        if config.get('Camera', 'encoding'):
            map['--encoding'] = config.get('Camera', 'encoding')
        if config.get('Camera', 'sharpness') != '0':
            map['--sharpness'] = config.get('Camera', 'sharpness')
        if config.get('Camera', 'quality') != '0':
            map['--quality'] = config.get('Camera', 'quality')
        if config.get('Camera', 'hflip') != '0':
            map['--hflip'] = None
        if config.get('Camera', 'vflip') != '0':
            map['--vflip'] = None
           
        return map


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
   
    def build(self):
        self.root = PiKamWidget()
        if self.config.get('Misc', 'splash') != '0' and os.path.exists('piKamSplash.jpg'):
            self.displayImage('piKamSplash.jpg')
        self.reconnect()
        return self.root
    
    def build_config(self, config):
        config.setdefaults('Server', {'hostname': 'localhost', 'port': '8000'}) 
        config.setdefaults('Camera', {'encoding': 'jpg', 'quality': 0, 'sharpness': 0, 'hflip': 0, 'vflip': 0})
        config.setdefaults('Misc',   {'carousel': 1, 'splash': 1})
        
    def build_settings(self, settings):
        # Javascript Object Notation
        settings.add_json_panel('PiKam App', self.config, data=SETTINGS_JSON_DATA)
            
    def on_config_change(self, config, section, key, value):
        if config is self.config:
            if section == 'Server':
                self.reconnect()
                
    def displayInfo(self, message, title='Info'):
        popContent = BoxLayout(orientation='vertical')
        popContent.add_widget(Label(text=message))
        popup = Popup(title=title,
                    content=popContent,
                    text_size=(len(message), None),
                    size_hint=(.8, .33))
        popContent.add_widget(Button(text='Close', size_hint=(1,.33), on_press=popup.dismiss))
        popup.open()

    def displayError(self, message, title='Error'):
        self.displayInfo(message, title)
        
    def displayProgress(self, value):
        self.root.downloadProgress.value += value
        
    def displayBusyWaiting(self, dt=None):
        if dt == None:
            print "schedule"
            self.lastProgressValue = 0
            self.root.downloadProgress.value = 0
            Clock.schedule_interval(self.displayBusyWaiting, 1 / 50.)
            return
        # Fake progress updates until the real updates happen
        
        if self.lastProgressValue == self.root.downloadProgress.value:
            self.lastProgressValue += 10000
            self.root.downloadProgress.value += 10000
            return True
        else:
            print "stop"
            return False
         
    def displayImage(self, filename):
        useCarousel = self.config.get('Misc', 'carousel') != '0'
        pyImg = PyImage.open(filename)
        pyImg.thumbnail((1024,1024), PyImage.ANTIALIAS)
        previewFilename = filename + '.thumb.jpg'
        pyImg.save(previewFilename)
        image = Image(source=previewFilename)
        if useCarousel:
            self.root.imageCarousel.add_widget(image)
            # Set the carousel to display the new image (could exhaust memory - perhaps only display last N)
            self.root.imageCarousel.index = len(self.root.imageCarousel.slides) - 1
        else:
            self.root.imageLayout.clear_widgets()
            self.root.imageLayout.add_widget(image)

    def on_connection(self, connection):
        self.displayInfo('Connected succesfully!')
        self.chdkConnection = connection  
        self.prepareCamera()
 
    def on_pause(self):
        reactor._mainLoopShutdown()
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
        # Turn the response string back nto a dictionary and see what it is
        result = cPickle.loads(message)
        if result['type'] == 'jpeg':
            # Save the image and add an internal copy to the GUI carousel.
            filename = result['name']
            with open(filename, 'wb') as imageFile:
                imageFile.write(result['data'])
            self.displayImage(filename)

        elif result['type'] == 'error':
            self.displayError(result['message'])
        else:
            self.displayError('Unexpected kind of message.')
        self.root.downloadProgress.value = 0

    def takeSnapshot(self):
        command = {}
        command['cmd'] = 'shoot'
        command['args'] = self.model.toMap(self.config)
        # Turn the dictionary into a string so it can be sent in Netstring format
        self.sendRemoteCommand(cPickle.dumps(command))
        self.displayBusyWaiting()
        
    def prepareCamera(self):
        #command = {'cmd': 'prepareCamera'}
        #self.sendRemoteCommand(cPickle.dumps(command))
        pass
        
    def reconnect(self):
        hostname = self.config.get('Server', 'hostname')
        port = self.config.getint('Server', 'port')
        reactor.connectTCP(hostname, port, PiKamClientFactory(self))
    
        
if __name__ == '__main__':
    PiKamApp().run()
