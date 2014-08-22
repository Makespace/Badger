Badger
======


The makespace badge printing machine


##Hardware

The tag hardware is from ib technology:

Universal socket board: http://www.ibtechnology.co.uk/products/universal-socket-board-product.htm

Tag module: http://www.ibtechnology.co.uk/products/hitag2-product.htm  It seems you need at least v1.1 of the firmware.

The printer is a Dymo Label 450

###Addition if you want to do the buttons

The Badger uses the DSR# pin of the USB - Serial chip (FT232RL) as an input for the buttons. If you just want a single button (for editing label, for example), you can connect it directly to that pin (Pin 9), with the other side of the button connected to 0V.

If you want to have two buttons, you need a multiplexer. Pin 2 (DTR#) drives the selection. See the "BadgerMux - Schematic.pdf" for a sketch of a circuit which works.

##Software

you'll need...

    sudo apt-get install python-tk python-wand

Plug in the label printer and install its drivers in the normal way. Set the orientation option to "Landscape".


If necessary, sort out RW access to the tag reader's serial port (the software will suggest ways to do that if it can't open the port).

On the Aspire One, we found that gnome-screensaver doesn't correctly reactivate the screen, so we removed it and used xscreensaver instead (you can google how to do that, if you need to.)

empty_badge.db needs to be copied to badge.db. It must exist in the same directory as dialog_tk.py, do_qr.py and tagreader4.py.

tagreader4.py is the program you need to have running. It starts the GUI interface (dialog_tk.py) as and when needed.

do_qr.py contains a class for the qr printing. 


Contact kim@spencejones.com if you have any questions or suggestions.
