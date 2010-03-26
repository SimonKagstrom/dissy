######################################################################
##
## Copyright (C) 2009,  Mads Chr. Olesen
##
## Author:        Mads Chr. Olesen <mads@mchro.dk>
## Description:   Infobox using WebKit
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import gtk
import webkit

class InfoBox(webkit.WebView):

    def __init__(self):
        webkit.WebView.__init__(self)

    def set_markup(self, markup):
        html = """
<html>
<head>
<style>
table { 
    border-collapse: collapse;
} 

td { 
    border: 1px solid black;
    padding: 0px 5px 0px 5px; /* pad right and left */
}
</style>
</head>
<body>
%s
</body></html>
""" % (markup)
        self.load_string(html, "text/html", "iso-8859-15", "")

        #Debugging
        if False:
            f = open('/tmp/dissy-infobox.html', 'w')
            f.write(html)
            f.close()
