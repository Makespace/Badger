#! /usr/bin/python
# -*- coding: iso-8859-1 -*-
# 
# use sqlite3 -- sudo apt-get install sqlite3 to install it
# 

import serial
import sqlite3 as sqlite

import cups
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from time import sleep
import subprocess

from subprocess import Popen, PIPE
from sys import argv

#from do_qr import _Do_qr

class sqlGet():
    def __init__(self):

        with sqlite.connect('badge.db') as con:
            
            cur = con.cursor()    
            cur.execute('SELECT SQLITE_VERSION()')
            
            data = cur.fetchone()
            
            print "SQLite version: %s" % data

            # cur.execute("DROP TABLE IF EXISTS Tags")
            # cur.execute("CREATE TABLE Tags(Tag INT, Name TEXT, Comment TEXT)")
            # #cur.execute("INSERT INTO Tags VALUES(x'0e14e31c', 'Aude', 'supergirl')")     # the "spare" test tag
            # cur.execute("INSERT INTO Tags VALUES(x'bb9c0b1c', 'Kim SJ', 'Owner: 3D printers, Wood Lathe')")

class tagReader():
    def __init__(self):
        #print chr(27) + "[2J" # clear the screen
        print "\x1b[2J\x1b[H"
        print "Tag reader v0.04"
        self.tempFileDir = "/dev/"

        try:
            self.ser = serial.Serial('/dev/ttyUSB0',9600, rtscts=1, timeout=0.1)
        except IOError as e:
            s=e[0]
            try:
                s.index('Permission denied')
                print "\nYou don't have permission to access the serial port.\nThe easy way to fix this is to add yourself to the group \"dialout\".\n"
                print "Alternatively you can fight UDEV...\nCreate a file called /etc/udev/rules.d/USB_serial.rules with the following contents:\n\nKERNEL==\"ttyUSB*\", MODE=\"0666\"\n"
                print "This will give public rw access to all your USB serial ports.\n"
            except:
                print "Error opening serial port: {0}".format(s)

        self.lastTag = None

        #define place to put temp files (in RAM for speed)
        self.tempFileDir = "/dev/shm/"

        # set up page size parameters - 89 x 36 mm
        self.w = 89 * mm
        self.h = 36 * mm

        ##########################################################
        # Printer initialisation
        ##########################################################

        self.conn = cups.Connection()

        # test to see if the label printer is installed
        self.printers = self.conn.getPrinters ()
        try:
            self.printers["DYMO-LabelWriter-450"]["device-uri"]
        except KeyError:
            print "Label printer not found"
            exit(1)


    def tryTag(self):
        # test the state of the tag reader,
        # return "None" if no tag present, or tag ID (in binary, four bytes)

        # We need to send the command soon after CTS becomes active (within 10mS)
        # so wait for that moment:
        while self.ser.getCTS():
            pass # wait if CTS was already active

        self.ser.write( "U")
        self.ser.flush()
        response = self.ser.read()
        if response == "":
            print "Warning: Serial timeout happened"
            return None
        if (ord(response) == 0xD6): # tag present
            return self.ser.read(4)
        if (ord(response) == 0xC0): # tag not present
            return None
        print "Warning: Unexpected response from tag reader: "+response.encode('hex')
        return None

    def seekTag(self):
        # Look for a genuine tag reading, and respond to it once for each touch
        # Debounces both arrival and departure of tag

        # the options for the badge cases
        def caseNoButtons():
            print "- Printing badge for {0}...".format(result[0])
            self.printBadge(name=result[0],comment = result[1] )
        def caseEditButtons():
            subprocess.call(["killall", "dialog_tk.py"])
            subprocess.Popen(['./dialog_tk.py',tag.encode('hex')])
        def caseQrCode():
            #print "Printing a QR code..."
            #Do_qr.print_qr(self,tag.encode('hex'))
            p1 = Popen(['qr',tag.encode('hex')], stdout=PIPE)
            p2 = Popen(['lp'], stdin=p1.stdout, stdout=PIPE)
            p1.stdout.close()

        def caseBusyBadge():
            print "both buttons pressed. Could this be 'busy' badge?"

        tag = self.tryTag()
        if tag == None:
            return None
        # so we have a real tag
        tag2 = self.tryTag() # read it again
        if tag2 == tag:
            # we beleive we have a real tag, correctly read, otherwise loop again
            result= self.lookup(tag)
            print tag.encode('hex'),
            if result != None:
                # do a pythonic case statement...
                {0:caseNoButtons, 1:caseEditButtons, 2:caseQrCode, 3:caseBusyBadge}[self.read_buttons()]()
            else:
                print "not in database" # so first time -- get input
                subprocess.call(["killall", "dialog_tk.py"])
                subprocess.Popen(['./dialog_tk.py',tag.encode('hex')])

            # wait until the tag goes away
            # might have to ignore a couple of "not there"s
            tagGone = False
            while not tagGone:
                tagGone = self.tryTag() == None and self.tryTag() == None and self.tryTag() == None # three blanks is convincing tag gone

 
    def read_buttons(self):
        # 0 -- neither button pressed
        # 1 -- Edit button pressed
        # 2 -- QR button pressed
        # 3 -- Both buttons pressed

        buttons = 0
        self.ser.setDTR(False)
        if self.ser.getDSR():
            buttons += 1
        self.ser.setDTR(True)
        if self.ser.getDSR():
            buttons += 2
        return buttons

    def lookup(self,tag):
        with sqlite.connect('badge.db') as con:
            
            cur = con.cursor()    
            cur.execute("SELECT Name, Comment FROM Tags WHERE Tag = x'"+tag.encode('hex')+"'")
            return cur.fetchone()

    def printBadge(self,name,comment):
        #####################################################
        # Use pdfgen to create our badge...
        #####################################################
        c = canvas.Canvas(self.tempFileDir+"tagbadge.pdf",pagesize=(self.w,self.h))

        # Now shrink font until name fits...
        fontSize = 60
        nameWidth = c.stringWidth(name,"Helvetica-Bold",60)
        if (nameWidth > (self.w * 0.9) ):
            fontSize = fontSize * self.w * 0.9 / nameWidth

        c.setFont("Helvetica-Bold",fontSize)
        c.drawCentredString(self.w/2,70-fontSize/2,name)

        c.setFont("Helvetica",14)

        c.translate(self.w/2,15)

        commentWidth = c.stringWidth(comment,"Helvetica-Bold",14)
        if (commentWidth > (self.w * 0.9) ):
            hScale = self.w * 0.9 / commentWidth
        else:
            hScale = 1
        c.scale(hScale,1)
        c.drawCentredString(0,0,comment)

        c.showPage()
        c.save()

        # ... and print it
        self.conn.printFile("DYMO-LabelWriter-450",self.tempFileDir+"tagbadge.pdf","Badge",{})


if __name__ == "__main__":
    t=tagReader()
    sql=sqlGet()
    while True:
        t.seekTag()
