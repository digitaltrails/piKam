# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# PiKamPicamServer.py - Picam server for PiKam 
#
# Copyright (C) 2013: Michael Hamilton
# The code is GPL 3.0(GNU General Public License) ( http://www.gnu.org/copyleft/gpl.html )
#
from twisted.internet import reactor, protocol, defer

import cPickle as Pickler
from datetime import datetime
import StringIO

import picam

from piKamServer import PiKamRequest, PiKamServerProtocal
from piKamServer import SCENE_OPTIONS,AWB_OPTIONS,METERING_OPTIONS,IMXFX_OPTIONS,COLFX_OPTIONS,ISO_OPTIONS,ENCODING_OPTIONS


class PiKamPicamServerProtocal(PiKamServerProtocal):
   
    shooting = False
    
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
            print 'bad message', cmd['cmd']
            msg = 'Invalid Command:' + cmd['cmd']
            self.transport.write(str(len(msg)) + ':' + msg + ',')             

    def connectionLost(self, reason):
        print "Client Connection Lost!"
        
    def prepareCamera(self, cmd):
        """Put the camera in to recording mode."""
        #self.osCommand(['/home/pi/chdkptp.sh', '-econnect', '-erec'])
        pass

    def shoot(self, cmd):
        while self.shooting:
            print 'sleeping'
            self._sleep(1)
        try:
            self.shooting = True
            request = cmd['args']
            print vars(request)
            imageType = request.encoding if request.encoding else 'jpg'
            imageFilename = 'IMG-' + datetime.now().isoformat().replace(':','_') + '.' + imageType
            imageType = request.encoding if request.encoding != 'jpg' else 'JPEG'
            replyMessageType = request.replyMessageType
            #print imageType, imageFilename

            picam.config.imageFX = IMXFX_OPTIONS.index(request.imxfx) if request.imxfx else 0
            picam.config.exposure = SCENE_OPTIONS.index(request.scene) if request.scene else 0
            picam.config.meterMode = METERING_OPTIONS.index(request.metering)
            picam.config.awbMode = AWB_OPTIONS.index(request.awb)
            picam.config.ISO = int(request.iso) if ISO_OPTIONS.index(request.iso) != 0 else 0
            
            picam.config.sharpness = int(request.sharpness) if request.sharpness else 0            # -100 to 100
            picam.config.contrast = int(request.contrast)  if request.contrast else 0               # -100 to 100
            picam.config.brightness = int(request.brightness)   if request.brightness else 0           #  0 to 100
            picam.config.saturation = int(request.saturation)  if request.saturation else 0             #  -100 to 100
            #picam.config.videoStabilisation = 0      # 0 or 1 (false or true)
            # EV seems to be mis-stated - adjust
            picam.config.exposureCompensation  = int(request.ev * 8)  if request.ev else 0  # -10 to +10 ?
            #print picam.config.exposureCompensation
            #picam.config.rotation = 90               # 0-359
            picam.config.hflip = int(request.hflip)  if request.hflip else 0                  # 0 or 1
            picam.config.vflip = int(request.vflip) if request.vflip else 0                   # 0 or 1
            #picam.config.shutterSpeed = 20000         # 0 = auto, otherwise the shutter speed in ms
            width = request.width if request.width else self.MAX_WIDTH
            height = request.height if request.height else self.MAX_HEIGHT
            quality = request.quality if request.quality else self.DEFAULT_QUALITY
            
            if request.zoomTimes > 1.0:
                sz = 1.0/request.zoomTimes
                picam.config.roi = [ .5 - sz/2.0, .5 - sz/2.0, sz, sz ] 
                #print picam.config.roi
            
            image = picam.takePhotoWithDetails(width,height,quality) 
            
            buffer = StringIO.StringIO()
            image.save(buffer, imageType)
            imageBinary = buffer.getvalue()
            buffer.close()
            #print imageFilename, str(len(imageBinary))
            if imageBinary:
                data = {'type':replyMessageType, 'name':imageFilename, 'data':imageBinary}
            else:
                print 'error'
                data = {'type':'error', 'message':'Problem reading captured file.'}
            # data = {'type':'error', 'message':'Problem during capture.'}
            # Turn the dictionary into a string so we can send it in Netstring format.
            message = Pickler.dumps(data)
            print replyMessageType, imageType, 'len=', str(len(message))
            # Return a Netstring message to the client - will include the jpeg if all went well
            self.transport.write(str(len(message)) + ':' + message + ',')
        finally:
            self.shooting = False
 
    def _sleep(secs):
        d = defer.Deferred()
        reactor.callLater(secs, d.callback, None)
        return d 
                        
def main():
    """This runs the protocol on port 8000"""
    factory = protocol.ServerFactory()
    factory.protocol = PiKamPicamServerProtocal
    reactor.listenTCP(8000,factory)
    reactor.run()

if __name__ == '__main__':
    main()
