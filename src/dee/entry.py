import os
from xdg.DesktopEntry import DesktopEntry
import gi
from gi.repository import GdkPixbuf, Gtk

def get_icon_pixbuf(icon, size):
    if os.path.isfile(icon):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, size, size)
            # work around failing to scale xpm's (gdk bug #686910)
            return pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.NEAREST)
        except:
            pass
    icon_theme = Gtk.IconTheme.get_default()
    if icon_theme.has_icon(icon):
        try:
            pixbuf = icon_theme.load_icon(icon, size,
                                          Gtk.IconLookupFlags.USE_BUILTIN)
            # force scale, even for wrong-sized images (gdk bug #686852)
            return pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.NEAREST)
        except:
            pass

    default = icon_theme.load_icon("image-missing", size,
                                      Gtk.IconLookupFlags.USE_BUILTIN)
    return default

class Entry(DesktopEntry):

    def __init__(self, filename=None):
        DesktopEntry.__init__(self, filename)
        self.is_modified = False

    def isModified(self):
        return self.is_modified

    def isReadOnly(self):
        """
        Return True if the entry's file is read-only for this user.
        """
        if self.filename and not os.access(self.filename, os.W_OK):
            return True
        return False

    def getIconPixbuf(self, size):
        """
        Render the icon to a GdkPixbuf for the icon at the specified sized.
        """
        icon = self.getIcon()
        return get_icon_pixbuf(icon, size)
