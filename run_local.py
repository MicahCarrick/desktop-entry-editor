#!/usr/bin/env python
import sys
import os

python_dir = "@pythondir@".replace("${prefix}", "@prefix@")
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'src'))

print sys.path

try:
    from dee.application import Application 
except ImportError, e:
    sys.exit(str(e))
 
if __name__ == "__main__":
    app = Application('desktop-entry-editor', 
                      '0-debug', 
                      os.path.join(os.path.dirname(__file__), 'data'),
                      debug=True)
    app.install_exception_hook()
    app.run()
