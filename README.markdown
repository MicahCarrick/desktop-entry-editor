Desktop Entry Editor
===========================================================

Desktop Entry Editor is a GUI application for editing and creating application
launchers for GNOME, KDE, XFCE, and any other desktop environment implementing
the [Desktop Entry Specification] [1] from freedesktop.org.

1. [Install](#install)
2. [Basic Use](#use)
1. [Bug Reports](#bugs)

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

* GLib development headers (Fedora `glib2-devel`, Ubuntu `libglib2.0-dev`)
* Autotools (`automake`, `autoconf`, `intltool`, `m4`, `gettext`)


### Build Instructions ###

    git clone https://github.com/MicahCarrick/desktop-entry-editor.git
    cd desktop-entry-editor
    aclocal -I m4
    intltoolize
    autoconf
    automake --add-missing
    ./configure
    make

Become root user (`su` or `sudo`) and then run:

    make install



Basic Use <a id="use"/>
-----------------------------------------------------------

The left-hand side of the Desktop Entry Editor interface contains a list
application launchers found on your system in [XDG_DATA_DIRS][9]. By default you
will only see application launchers for which you have write permissions. To
see all application launchers, you can select `View > Show read-only-files`.

Selecting an application launcher in the list will open it in the editing area.

As a regular user, the ideal place to save your application launchers is in
`~/.local/share/applications` which is the default location used by Desktop
Entry Editor.

The 'Basic' tab allows you to edit basic information that most people want to
use when creating an application launcher. The 'Advanced' tab allows you to
edit any of the recognized [Desktop Entry keys][10]. As the 'Advanced' tab
allows free-form typing, you should validate your changes by selecting
`Tools > Validate` before you save.

To get your application launcher to appear in the system menu, overview, or
search, you can try running the following command as root:

    update-desktop-database

That will not work for all desktop environments and you may need to log out and
then log back in before your application launcher is available.



Bug Reports <a id="bugs"/>
-----------------------------------------------------------

Report bugs on the GitHub [Issues Page][8].


[1]: http://standards.freedesktop.org/desktop-entry-spec/latest/
[2]: screenshot.png
[3]: https://github.com/MicahCarrick/desktop-entry-editor/releases
[4]: http://www.gtk.org
[5]: http://ftp.gnome.org/pub/GNOME/sources/pygobject/3.0/
[6]: http://ftp.acc.umu.se/pub/gnome/sources/gtksourceview/
[7]: http://www.freedesktop.org/wiki/Software/pyxdg
[8]: https://github.com/MicahCarrick/desktop-entry-editor/issues
[9]: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html
[10]: http://standards.freedesktop.org/desktop-entry-spec/latest/ar01s05.html
