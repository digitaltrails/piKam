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
import re
from datetime import datetime

class PiKamServerProtocal(basic.NetstringReceiver):
    """Uses Netstring format, for example '20:this message 20 long,'"""
    
    fileRe = re.compile('>([^.]+.JPG)', re.MULTILINE)  
    
    # Max message/jpg size.
    MAX_LENGTH = 100000000
        
    def stringReceived(self, data):
        """Process decoded Netstring message received from a client."""
        # Turn the received string back into a dictionary.
        print data
        cmd = Pickler.loads(data)
        # Retreive the command from the dictionary
        if cmd['cmd'] == 'shoot':
            self.shoot(cmd)
        elif cmd['cmd'] == 'prepareCamera':
            self.prepareCamera(cmd)
        else:
            msg = 'Invalid Command:' + cmd['cmd']
            self.transport.write(str(len(msg)) + ':' + msg + ',')             
            
    def shoot(self, cmd):
        imageType = cmd['args']['--encoding'] if cmd['args']['--encoding'] else 'jpg'
        imageFilename = 'IMG-' + datetime.now().isoformat().replace(':','_') + '.' + imageType
        args = sum([[k] if v == None else [k,str(v)] for k,v in cmd['args'].iteritems()], [])
        raspistillCmd = ['raspistill', '-o', imageFilename, '-n'] + args
        
        output, err, rc = self.osCommand(raspistillCmd)
        print output
        print err
        if rc == 0:
            jpegBinary = None
            print imageFilename
            with open(imageFilename, 'rb') as jpegFile:
                jpegBinary = jpegFile.read()
            if jpegBinary:
                data = {'type':'jpeg', 'name':imageFilename, 'data':jpegBinary}
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
