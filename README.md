# piKam - Raspberry Pi Kivy User Interface

The piKam python Kivy application provides a remote interface
to a Raspberry Pi camera.  You can run piKam on any supported
Kivy platform and remotely drive a camera on a Raspberry Pi.

<img src="https://raw.github.com/digitaltrails/piKam/master/screenshot.jpg">

## Warnings/Issues:
* No security.
* No live view.
* GUI keeps all images in memory until it is exited.
* Running multiple raspistills at the same time can cause the camera to lock up.

  
## Prerequisites

### On your RaspberryPi - assuming Raspbian
Install the python-twisted package (used for client/server networking).

PiKam inclues a server that uses the raspistill command to drive the 
camera.  If you setup your Raspberry Pi so that raspistill works,
then piKam shold work too.

##### Optional picam support
I've included an alternate server that directly accesses
the camera via Sean Ashton's picam module.  If you wish to use 
the picam module then follow Sean's installation instructions at  https://github.com/ashtons/picam/blob/master/README.md

Picam requires the python image library, which can be
installed by running the following command:
  
   sudo apt-get install python-imaging-tk

### On your selected Kivy client platform 

I use piKam on Linux and Android, but it would likely run on
any platform supported by Kivy.

##### Linux Kivy Client:
  Install Kivy - most distributions seem to have a kivy package available. 
  On OpenSUSE this seemed to install everything needed including Twisted.

##### Android Kivy Client:
  Install the "Kivy Launcher" app from the Play Store.
     
 
## Install piKam and Test

### On your Raspberry Pi
Copy piKamServer.py to your Raspberry Pi. Start the server - at the shell prompt:  

         python piKamServer.py
         
If you wish to use the picam python module for direct camera access, then also 
copy piKamPicamServer.py to your Raspberry Pi and run that instead:
     
         python piKamPicamServer.py
### On your selected Kivy client platform 

##### Linux Kivy Client: 

1. Create a folder called piKam (or anything you prefer).
Copy all the piKam files to this folder. 
2. In a shell, cd to the piKam folder and enter: 

   ```
   python piKam.py
   ```
   
   A GUI should fire up.

3. Press F1 to bring up the piKam settings dialog. 
4. Set the address of you RaspberryPi and close settings.
5. See if you can connect and "Capture" a photo.
    
##### Android Kivy Client: 
1. Find where "Kivy Launcher" put it's apps folder.
   * Lets say you find that Kivy Launcher is using /sdcard0/kivy/
   * Create a sub-folder /sdcard0/kivy/pikam 
2. Copy all the piKam files into this folder (skip piKamServer if you wish).
3. Start the Kivy Launcher, it should list a piKam app, tap on it. A GUI should fire up.
4. Tap the standard Android settings button/icon to bring up the piKam settings dialog. 
5. Set the address of you RaspberryPi and close settings.
7. See if you can connect and take a photo.

##### Other clients

Kivy runs on a wide variety of platforms, installation would probably be similar to Linux.

## Controls:
Mostly obvious.
Swipe left right on the image to goto prev/next.    
Photos are written to the client install folder.
