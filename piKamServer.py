# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# PiKamServer.py 
#
# Copyright (C) 2013: Michael Hamilton
# The code is GPL 3.0(GNU General Public License) ( http://www.gnu.org/copyleft/gpl.html )
#
from twisted.internet import reactor, protocol
from twisted.protocols import basic

import subprocess
import cPickle as Pickler
from datetime import datetime

# Enable a test image if not running on RaspberryPi or the Pi lacks a camera
TEST_IMAGE = None
#TEST_IMAGE = 'piKamSplash.jpg'


SCENE_OPTIONS = "off,auto,night,nightpreview,backlight,spotlight,sports,snow,beach,verylong,fixedfps,antishake,fireworks".split(',')
AWB_OPTIONS = "off,auto,sun,cloud,shade,tungsten,fluorescent,incandescent,flash,horizon".split(',')
METERING_OPTIONS = "average,spot,backlit,matrix".split(',')
IMXFX_OPTIONS = "none,negative,solarise,sketch,denoise,emboss,oilpaint,hatch,gpen,pastel,watercolour,film,blur,saturation,colourswap,washedout,posterise,colourpoint,colourbalance,cartoon".split(',')
COLFX_OPTIONS = "none,U,V".split(',')
ISO_OPTIONS = "auto,50,100,200,400,800".split(",")
ENCODING_OPTIONS = "jpg,bmp,gif,png".split(",")

class PiKamRequest():
    
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

    encoding = None
    sharpness = None
    quality = None
    hflip = None
    vflip = None
    

class PiKamServerProtocal(basic.NetstringReceiver):
    """Uses Netstring format, for example '20:this message 20 long,'"""
        
    # Max message/jpg size.
    MAX_LENGTH = 100000000
        
    def stringReceived(self, data):
        """Process decoded Netstring message received from a client."""
        # Turn the received string back into a dictionary.
        #print data
        cmd = Pickler.loads(data)
        # Retreive the command from the dictionary
        if cmd['cmd'] == 'shoot':
            self.shoot(cmd)
        elif cmd['cmd'] == 'prepareCamera':
            self.prepareCamera(cmd)
        else:
            msg = 'Invalid Command:' + cmd['cmd']
            self.transport.write(str(len(msg)) + ':' + msg + ',')             
            
    def createShootCommand(self, request):
        imageType = request.encoding if request.encoding else 'jpg'
        imageFilename = 'IMG-' + datetime.now().isoformat().replace(':','_') + '.' + imageType
         # EV seems to be mis-stated - adjust
        args = [ 
            'raspistill', '-n',
            '-o', imageFilename,
            '--ISO', str(request.iso), 
            '--ev', str(request.ev * 6), 
            '--brightness', str(request.brightness), 
            '--contrast', str(request.contrast), 
            '--saturation', str(request.saturation), 
            '--awb', request.awb,
            '--metering', request.metering,
            #'-t', '1',
            ]
        if request.zoomTimes > 1.0:
            sz = 1.0/request.zoomTimes
            roi = [ .5 - sz/2.0, .5 - sz/2.0, sz, sz ] 
            args += ('--roi', ','.join([str(v) for v in roi]))
        if request.imxfx != 'none':
            args += ('--imxfx', request.imxfx)
        if request.colfx != 'none':
            args += ('--colfx', request.colfx)
        if request.scene != 'off':
            args += ('--exposure', request.scene)
        if request.encoding:
            args += ('--encoding', request.encoding)
        else:
            args += ('--encoding', 'jpg')
        if request.sharpness:
            args += ('--sharpness', request.sharpness)
        if request.quality:
            args += ('--quality', request.quality)
        if request.hflip:
            args += ('--hflip', request.hflip)
        if request.vflip:
            args += ('--vflip', request.vflip)  
        return args, imageFilename, imageType

    def shoot(self, cmd):
        raspistillCmd, imageFilename, imageType = self.createShootCommand(cmd['args']) 
        output, err, rc = self.osCommand(raspistillCmd if not TEST_IMAGE else [ 'sleep', '2' ])            
        print output
        print err

        if rc == 0:
            imageBinary = None
            print imageFilename
            with open(imageFilename if not TEST_IMAGE else TEST_IMAGE, 'rb') as jpegFile:
                imageBinary = jpegFile.read()
            if imageBinary:
                data = {'type':'image', 'name':imageFilename, 'data':imageBinary}
            else:
                data = {'type':'error', 'message':'Problem reading captured file.'}
        else:
            data = {'type':'error', 'message':'Problem during capture.'}
        # Turn the dictionary into a string so we can send it in Netstring format.
        message = Pickler.dumps(data)
        print str(len(message))
        # Return a Netstring message to the client - will include the jpeg if all went well
        self.transport.write(str(len(message)) + ':' + message + ',')
 
    def prepareCamera(self, cmd):
        """Put the camera in to recording mode."""
        #self.osCommand(['/home/pi/chdkptp.sh', '-econnect', '-erec'])
        pass

    def osCommand(self, osCmd):
        print osCmd
        p = subprocess.Popen(osCmd, stdout=subprocess.PIPE)
        output, err = p.communicate()
        rc = p.returncode
        print "------"
        print "output:>>>", output, "<<<"
        print "error:[[[", err, "]]]"
        return (output, err, rc)
       
def main():
    """This runs the protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = PiKamServerProtocal
    reactor.listenTCP(8000,factory)
    reactor.run()

if __name__ == '__main__':
    main()
