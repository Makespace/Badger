#! /usr/bin/python
# -*- coding: iso-8859-1 -*-
# 
# TODO:
#   Wire up switches and test the "edit" feature
#   Add QR printing option
#   re-implement ad-hoc label
#   Re-size edit window default
#   See if it's possible to run only a single instance of the program
#   and/or update fields when app regains focus. (Hard, to avoid losing edits)

import Tkinter

import cups
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

#import wand
from wand.image import Image as WandImage
# sudo apt-get install libmagickwand-dev
# sudo pip install Wand
 
import sqlite3 as sqlite
import sys

class badger_tk(Tkinter.Tk):
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        #define place to put temp files (in RAM for speed)
        self.tempFileDir = "/dev/shm/"

        # set up page size parameters - 89 x 36 mm
        self.w = 89 * mm
        self.h = 36 * mm

        # temporary tagString
        #self.tagString = 'bb9c0b1c'

        if len(sys.argv) < 2:
            exit(1)
        if len(sys.argv) == 1:
            print "This should be ad-hoc label but not implemented yet"

        tagString = sys.argv[1]
        tagString2 = hex(int(tagString,16))[2:] # drop leading "0x"
        if tagString2[-1:] == "L":
            tagString2 = tagString2[:-1] # drop final "L"
        if tagString != ("00000000"+tagString2)[-8:]:
            print "Bad tag number: ", tagString, ("00000000"+hex(int(tagString,16))[2:-1])[-8:]
            exit(1)
        else:
            print "using tagString "+tagString
            self.tagString = tagString



        ###################################################################
        # interrogate the database
        ###################################################################
        with sqlite.connect('badge.db') as con:
            
            cur = con.cursor()    
            cur.execute("SELECT Name, Comment FROM Tags WHERE Tag = x'"+self.tagString+"'")
            result = cur.fetchone()
            self.updating = result != None
            if self.updating:
                name = result[0]
                comment = result[1]
            else:
                name = comment = ""

        ###################################################################
        # Create the UI
        ###################################################################

        self.grid()
        self.bind("<Return>", self.OnPressEnter)
        self.bind("<FocusOut>", self.PreviewOnEvent)

        # Application title
        Tkinter.Label(self, anchor="w", text="Makespace badger data update").grid(column=0,row=0,columnspan=3,sticky='EW')

        # Tag being edited
        Tkinter.Label(self,anchor="w", text="Editing tag ").grid(column=0,row=1,sticky='EW')
        Tkinter.Label(self,anchor="w", text=self.tagString, fg='red').grid(column=1,row=1,sticky='EW')
        if not self.updating:
                    self.newLabel = Tkinter.Label(self,anchor="w", text="* NEW *", fg='red')
                    self.newLabel.grid(column=2,row=1,sticky='EW')

        # name field
        Tkinter.Label(self,anchor="w", text="Name").grid(column=0,row=2,sticky='EW')

        self.nameEntry = Tkinter.Entry(self)
        self.nameEntry.grid(column=1,row=2,columnspan=2,sticky='EW')
        self.nameEntry.bind("FocusIn", lambda: self.nameEntry.selection_from(0))
        self.nameEntry.insert(0,name)

        # "nameClear" button
        Tkinter.Button(self,text=u"x", command=lambda:self.OnClrClick(self.nameEntry), takefocus=0).grid(column=4,row=2)


        # comment field
        Tkinter.Label(self,anchor="w", text="Comment").grid(column=0,row=3,sticky='EW')

        self.commentEntry = Tkinter.Entry(self)
        self.commentEntry.grid(column=1,row=3,columnspan=2,sticky='EW')
        self.commentEntry.bind("FocusIn", lambda: self.commentEntry.selection_from(0))
        self.commentEntry.insert(0,comment)

        # "commentClear" button
        Tkinter.Button(self,text=u"x", command=lambda:self.OnClrClick(self.commentEntry).focus_set(), takefocus=0).grid(column=4,row=3)

        # preview window
        Tkinter.Label(self, anchor="w", text="Preview:").grid(column=0,row=4,columnspan=5,sticky='W')
        # create the canvas, size in pixels
        self.previewPane = Tkinter.Canvas(width = self.w, height = self.h)
        self.previewPane.grid(column=0, columnspan=5,row=5)

        # "print" button
        self.printButton = Tkinter.Button(self,text=u"Save and Print", command=self.OnPrintButtonClick)
        self.printButton.grid(column=1,row=6, columnspan=2, sticky="")
        self.printButton.bind("<Return>", self.OnPrintEnter)

        # generate preview files
        self.DoPreview()

        self.grid_columnconfigure(1,weight=1)
        self.grid_columnconfigure(2,weight=1)

        # fix vertical size
        self.resizable(True,False)

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

        self.nameEntry.focus_set()

    def OnClrClick(self,fld):
        fld.delete(0, "end")
        fld.focus_set()

    def PreviewOnEvent(self,event):
        self.DoPreview()

    def DoPreview(self):

        #####################################################
        # Use pdfgen to create our badge...
        #####################################################

        name=self.nameEntry.get()
        comment = self.commentEntry.get()

        c = canvas.Canvas(self.tempFileDir+"badge.pdf",pagesize=(self.w,self.h))

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

        #############################################################
        # now create and view displayable version of the image
        #############################################################

        with WandImage(filename=self.tempFileDir+'badge.pdf') as im:
            im.format = "gif"
            im.alpha_channel = False
            im.save(filename=self.tempFileDir+'badge.gif')
        # load the .gif image file
        self.gif1 = Tkinter.PhotoImage(file = self.tempFileDir+'badge.gif')
        # put gif image on canvas, centered
        self.previewPane.create_image(self.w/2, self.h/2, image = self.gif1, anchor = "center")

    def OnPrintEnter(self,event):
        #############################################################
        # now print label and save values to db
        #############################################################
        # DoPreview not needed in this case, because button has focus, so must have done preview when
        # focus left another field.
        # ...so do the print
        self.conn.printFile("DYMO-LabelWriter-450",self.tempFileDir+"badge.pdf","Badge",{})
        # ...and the save

        name=self.nameEntry.get()
        comment = self.commentEntry.get()
        
        with sqlite.connect('badge.db') as con:
            
            cur = con.cursor()
            if self.updating:
                t = (name, comment)
                # seems you can't use variables in a where clause...
                cur.execute("UPDATE Tags SET Name=?, Comment=? WHERE Tag=x'"+self.tagString+"'", t)
            else:
                t = (name, comment)
                cur.execute("INSERT INTO Tags VALUES(x'"+self.tagString+"', ?, ?)", t)
                self.updating = True
                # clear the "new" field by destroying '* NEW *' label
                self.newLabel.destroy()

        self.destroy()

        #return("break") # prevent propagation of <Return> event -- as a result, focus stays on the button

    def OnPrintButtonClick(self):
    	self.DoPreview() # This is necessary in the case where you click Print without the focus leaving one of the Entry fields.
        self.OnPrintEnter(None) # now can process as if <Enter> has been pressed.


    def OnPressEnter(self,event):
        self.DoPreview()
        event.widget.tk_focusNext().focus()


if __name__ == "__main__":
    app = badger_tk(None)
    app.title('Makespace Badger (database update) v0.01')
    app.mainloop()
