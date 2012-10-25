import os
from xdg.DesktopEntry import DesktopEntry
from gi.repository import GdkPixbuf, Gtk

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
        icon_theme = Gtk.IconTheme.get_default()
        default = icon_theme.load_icon(Gtk.STOCK_MISSING_IMAGE, size, 
                                          Gtk.IconLookupFlags.USE_BUILTIN)
        if os.path.exists(icon):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, size, size)
            except:
                pixbuf = default
        elif icon_theme.has_icon(icon):
            try:
                pixbuf = icon_theme.load_icon(icon, size, 
                                              Gtk.IconLookupFlags.USE_BUILTIN)
            except:
                pixbuf = default
        else:
            pixbuf = default
        
        return pixbuf
