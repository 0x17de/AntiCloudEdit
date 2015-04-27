# AntiCloudEdit
Webserver based IDE for easy-to-use remote python development on e.g raspberry pi / intel edison or other devices.

Many devices now think cloud platforms are required to code on your device.
Just use this webservice to develop your python/html/text applications - makefile support would be also a possibility in the future, as the syntax highlighter already supports various file types.
It will work on any python supporting platform with a network connection running - so that you can connect via web browser (be sure to not use this service in open networks yet!).

## Hotkeys
The edit pane has built-in hotkeys:
- Ctrl+F : Find
- Ctrl+H : Find & Replace
- Ctrl+L : Goto line
- ... please see ace.js homepage for an entire list.

## Preview
![preview](http://www.icetruck.de/0/pics/anticloudedit.png)

## Features planned or already existent
(*: working yet)
- * create files
- * edit and save files
- * switch files (click around in tree on the left)
- * resize views
- * delete files and folders
- * download on any file or folder (try out the context menu on tree items on the left)
- * syntax highlighting
- * upload zip files and extract on target
- run scripts on remote device and see output in browser
- security features (basic auth + ssl)

## Used external libraries
- http://www.cherrypy.org/
- http://jquery.com/
- http://ace.c9.io/
- https://github.com/medialize/jQuery-contextMenu
- https://github.com/jcubic/jquery.splitter
- https://blueimp.github.io/jQuery-File-Upload/
