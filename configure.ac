dnl minimum required version of autoconf

AC_PREREQ([2.60])

dnl initialize autoconf

AC_INIT([Desktop Entry Editor],
        [0.1],
        [https://github.com/Quixotix/desktop-entry-editor/issues],
        [desktop-entry-editor],
        [https://github.com/Quixotix/desktop-entry-editor])

AC_CONFIG_SRCDIR([src/dee/application.py])
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE

dnl check for required pythonmodules

AM_PATH_PYTHON([2.5])
AX_PYTHON_MODULE([xdg], [pyxdg])
AX_PYTHON_MODULE([gi.repository], [pygobject3])
AX_PYTHON_MODULE([gi.repository.GObject], [glib2])
AX_PYTHON_MODULE([gi.repository.Pango], [pango])
AX_PYTHON_MODULE([gi.repository.Gtk], [gtk3])
AX_PYTHON_MODULE([gi.repository.GtkSource], [gtksourceview3])

dnl check for optional python modules


dnl gettext
IT_PROG_INTLTOOL

dnl generate makefiles
AC_OUTPUT([
Makefile
data/Makefile
data/desktop-entry-editor.desktop
po/Makefile
src/Makefile
src/desktop-entry-editor
])

