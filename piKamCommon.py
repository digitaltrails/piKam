# -*- coding: utf-8 -*-
#!/usr/bin/env python
#
# PiKamPicamServer.py - Picam server for PiKam 
#
# Copyright (C) 2014: Michael Hamilton
# The code is GPL 3.0(GNU General Public License) ( http://www.gnu.org/copyleft/gpl.html )
#


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
    
    width = 0
    height = 0 
 
    replyMessageType = "image" 
