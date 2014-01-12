# piKam - Raspberry Pi Kivy User Interface

## Recent changes
#### 2014/01/12  
* Now with live/zombie preview. 
* Eliminated to need to write thumbnails and previews to disk.
* Adjusted +-ev values (the docs for raspistill seem wrong on value range).
* New piKamCommon.py to install on the client and server.

## Introduction

The piKam python Kivy application provides a remote interface
to a Raspberry Pi camera.  You can run piKam on any supported
Kivy platform (Linux, Android, Windows, etc) and remotely 
drive the camera on a Raspberry Pi.

<img src="https://raw.github.com/digitaltrails/piKam/master/screenshot.jpg">&nbsp;&nbsp;&nbsp;<img src="https://raw.github.com/digitaltrails/piKam/master/screenshot2.jpg">

## Warnings/Issues:
* No security, no encryption (if your network has other users, they can also connect to the server).
* Running multiple raspistills at the same time can cause the camera to lock up.
* The picam-based server's zoom isn't fully working.
* The live view is semi-live, it's slow, perhaps a zombie-view more than a live-view.
* Kivy settings don't seem to value restrictions and I haven't yet coded any sanity checks of my own.
* Switching to scene mode Auto seems to improve brightness/contrast.
* -ev doesn't seem to do much.

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
Copy piKamServer.py and piKamCommon.py to your Raspberry Pi. Start the server - at the shell prompt:  

         python piKamServer.py
         
If you wish to use the picam python module for direct camera access, then also 
copy piKamPicamServer.py to your Raspberry Pi and run that instead:
     
         python piKamPicamServer.py
         
The picam version is faster and probably to be preferred.

### On your selected Kivy client platform 

##### Linux Kivy Client: 

1. Create a folder called piKam (or anything you prefer).
Copy all the piKam files to this folder. 
2. In a shell, cd to the piKam folder and enter: 

   ```
   python main.py
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

* Swipe left right on the image to goto prev/next on the image carousel.  The 
  carousel is limited to the 10 most recent images.
* Photos are written to the client install folder.
* Take a look at the settings menu for options/customisations (F1 on Linux, Tap Settings on Android).
* If live view is enabled, the rightmost image on the carousel will display 
  a low quality preview with the camera settings applied. If you move the
  view away from the rightmost image, the the live view network traffic 
  suspends until the rightmost image is again visible.  
* The way live view is coded may mean you don't get much/any time to review a picture, 
  but you can always scroll the carousel to suspend live view and 
  review past images.
