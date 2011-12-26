Desktop Entry Editor
===========================================================

Desktop Entry Editor is a GUI application for editing and creating application
launchers for GNOME, KDE, XFCE, and any other desktop environment implementing
the [Desktop Entry Specification] [1] from freedesktop.org.

1. [Install](#install)

![Desktop Entry Editor running on GNOME 3.2 in Fedora 16][2]



Install <a id="install"/>
-----------------------------------------------------------

### Requirements ###

The following packages are needed to run Desktop Entry Editor. Most newer Linux 
distributions will already have these packages installed or available in their 
software repositories.

* [GTK+ 3][4] (Fedora `gtk3`, Ubuntu `libgtk-3-0`)
* [PyGObject 3][5] (Fedora `pygobject3`, Ubuntu `python-gobject`)
* [GtkSourceView 3][6] (Fedora `gtksourceview3`, Ubuntu `libgtksourceview-3.0`)
* [PyXDG][7] (Fedora `pyxdg`, Ubuntu `python-xdg`)

If you are going to be building Desktop entry Editor from source you may need
these additional packages:

* GLib development headers (Fedora `glib2-devel`, Ubuntu `libglib2-dev`)
* Translation tools `intltool`


### Build Current Release from Source ###

Download the latest release from the [Downloads Page][3] and then run:
    
    tar -xzf desktop-entry-editor-x.x.x.tar.gz
    cd desktop-entry-editor-x.x.x
    ./configure
    make

_Note: replace `x.x.x` with the version number from the file you downloaded._

Become root user (`su` or `sudo`) and then run:

    make install
    

### Build Development Version from Source ###

    git clone https://github.com/Quixotix/desktop-entry-editor.git
    cd desktop-entry-editor
    aclocal -I m4
    intltoolize
    autoconf
    automake --add-missing
    ./configure
    make

Become root user (`su` or `sudo`) and then run:

    make install



Bug Reports <a id="bugs"/>
-----------------------------------------------------------

Report bugs on the GitHub [Issues Page][8].

    
[1]: http://standards.freedesktop.org/desktop-entry-spec/latest/
[2]: http://static.micahcarrick.com/media/images/desktop-entry-editor/desktop-entry-editor-basic.png
[3]: https://github.com/Quixotix/desktop-entry-editor/downloads
[4]: http://www.gtk.org
[5]: http://ftp.gnome.org/pub/GNOME/sources/pygobject/3.0/
[6]: http://ftp.acc.umu.se/pub/gnome/sources/gtksourceview/
[7]: http://www.freedesktop.org/wiki/Software/pyxdg
[8]: https://github.com/Quixotix/desktop-entry-editor/issues


