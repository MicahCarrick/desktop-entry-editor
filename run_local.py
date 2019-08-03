#!/usr/bin/env python
import signal
import sys
import os

python_dir = "@pythondir@".replace("${prefix}", "@prefix@")
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'src'))

print (sys.path)

try:
    from dee.application import Application 
except ImportError as e:
    sys.exit(str(e))
 
if __name__ == "__main__":
    # work around Gtk.main disabling ctrl-c (gnome bug #622084)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = Application('desktop-entry-editor', 
                      '0-debug', 
                      os.path.join(os.path.dirname(__file__), 'data'),
                      debug=True)
    app.install_exception_hook()
    app.run()
