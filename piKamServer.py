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
 
class PiKamServerProtocal(basic.NetstringReceiver):
    """Uses Netstring format, for example '20:this message 20 long,'"""
        
    # Max message/jpg size.
    MAX_LENGTH = 100000000
    MAX_WIDTH = 2592
    MAX_HEIGHT = 1944
    DEFAULT_QUALITY = 85
        
    def stringReceived(self, data):
        """Process decoded Netstring message received from a client."""
        # Turn the received string back into a dictionary.
        #print data
        cmd = Pickler.loads(data)
        # Retreive the command from the dictionary
        if cmd['cmd'] == 'shoot':
            imageFilename, imageBinary, imageType, replyMessageType = self._takePhoto(cmd['args'])
            self.transmitPhoto(imageFilename, imageBinary, replyMessageType)
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
            args += ('--quality', str(request.quality))
        if request.hflip:
            args += ('--hflip', request.hflip)
        if request.vflip:
            args += ('--vflip', request.vflip)  
        if request.width:
            args += ('--width', str(request.width))
        if request.height:
            args += ('--height', str(request.height))
        replyMessageType = request.replyMessageType
        return args, imageFilename, imageType, replyMessageType

    def transmitPhoto(self, imageFilename, imageBinary, replyMessageType):
        if imageBinary != None:
            data = {'type':replyMessageType, 'name':imageFilename, 'data':imageBinary}
        else:
            data = {'type':'error', 'message':'Problem during capture.'}
        # Turn the dictionary into a string so we can send it in Netstring format.
        message = Pickler.dumps(data)
        print str(len(message))
        # Return a Netstring message to the client - will include the jpeg if all went well
        self.transport.write(str(len(message)) + ':' + message + ',')

    def takePhoto(self, parameters):
        return self._takePhoto(parameters, returnPyImage=True)
        
    def _takePhoto(self, parameters, returnPyImage=False):
        imageBinary = None
        raspistillCmd, imageFilename, imageType, replyMessageType = self.createShootCommand(parameters) 
        output, err, rc = self.osCommand(raspistillCmd if not TEST_IMAGE else [ 'sleep', '2' ])            
        print output
        print err           
        if rc == 0:
            if returnPyImage:
                print 'py'
                import Image as PyImage
                pyImg = PyImage.open(imageFilename if not TEST_IMAGE else TEST_IMAGE)
                return imageFilename, pyImg, imageType, replyMessageType
            print 'npy'
            print imageFilename
            with open(imageFilename if not TEST_IMAGE else TEST_IMAGE, 'rb') as imageFile:
                imageBinary = imageFile.read()
        return imageFilename, imageBinary, imageType, replyMessageType
        
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
