Badger
======

Software for the makespace badge printing mahine

you'll need...

    sudo apt-get install python-tk python-wand

Plug in the Dymo Label 450 printer and install its drivers in the normal way. Set the orientation option to "Landscape".

If necessary, sort out RW access to the tag reader's serial port (the software will suggest ways to do that if it can't open the port).

On the Aspire One, we found that gnome-screensaver doesn't correctly reactivate the screen, so we removed it and used xscreensaver instead (you can google how to do that, if you need to.)

Contact kim@spencejones.com if you have any questions of suggestions.
