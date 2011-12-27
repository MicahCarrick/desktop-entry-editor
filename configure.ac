dnl minimum required version of autoconf

AC_PREREQ([2.60])

dnl initialize autoconf

AC_INIT([Desktop Entry Editor],
        [0.1.1],
        [https://github.com/Quixotix/desktop-entry-editor/issues],
        [desktop-entry-editor],
        [https://github.com/Quixotix/desktop-entry-editor])

AC_CONFIG_SRCDIR([src/dee/application.py])
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE

dnl check for glib2 (required for GLIB_GSETTINGS macro to work)

PKG_CHECK_MODULES([GLIB], [glib-2.0 >= 2.28])

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

IT_PROG_INTLTOOL([0.35.0])

GETTEXT_PACKAGE=desktop-entry-editor
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE, "$GETTEXT_PACKAGE", [The gettext package])
AM_GLIB_GNU_GETTEXT

dnl GSettings

GLIB_GSETTINGS

dnl generate output

AC_OUTPUT([
Makefile
data/Makefile
data/desktop-entry-editor.desktop
data/icons/Makefile
data/icons/hicolor/Makefile
data/icons/hicolor/16x16/Makefile
data/icons/hicolor/16x16/apps/Makefile
data/icons/hicolor/22x22/Makefile
data/icons/hicolor/22x22/apps/Makefile
data/icons/hicolor/24x24/Makefile
data/icons/hicolor/24x24/apps/Makefile
data/icons/hicolor/32x32/Makefile
data/icons/hicolor/32x32/apps/Makefile
data/icons/hicolor/48x48/Makefile
data/icons/hicolor/48x48/apps/Makefile
data/icons/hicolor/scalable/Makefile
data/icons/hicolor/scalable/apps/Makefile
data/ui/Makefile
po/Makefile.in
src/Makefile
src/desktop-entry-editor
src/dee/Makefile
])

