#! /usr/bin/python
#
# to make this work:
#    sudo apt-get install libcups2-dev python-dev
#    (sudo) pip install qrcode pillow pycups
#    
# label size 36 x 89 mm @ 300 dpi
# -> height = 36 * 300/25.4 * 90% ~= 380 px
# 21 rows + 8 for the margin = 29 rows, so 12px/row

from sys import argv

from qrcode import QRCode
from qrcode.constants import *

from subprocess import Popen, PIPE


class Do_qr:
    printer_name = "DYMO-LabelWriter-450"
    # printer_name = "Eastman-Kodak-Company-KODAK-ESP-C310-AiO"

    def print_qr(self, data):

        qr = QRCode(version=None,
                    error_correction=ERROR_CORRECT_H,
                    box_size=20
                   )
        qr.add_data(data)

        qr.make(fit=True) # Generate the QRCode itself

        # im contains a PIL.Image.Image object
        im = qr.make_image()
        prntr = Popen(["lp", "-s", "-d%s" % self.printer_name], stdin = PIPE, stdout = None, stderr = None)
        ## To send it to the printer
        im.save(prntr.stdin)
        # wait for process to do its stuff 
        prntr.communicate()
if __name__=="__main__":
    if len(argv) != 2:
        exit("Syntax: do_qr.py {data}")
    a=Do_qr()
    a.print_qr(argv[1])
