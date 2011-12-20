import os
from xdg.DesktopEntry import DesktopEntry
from gi.repository import GdkPixbuf, Gtk

class Entry(DesktopEntry):
       
    def getIconPixbuf(self, size):
        """
        Render the icon to a GdkPixbuf for the icon at the specified sized.
        """
        icon = self.getIcon()
        icon_theme = Gtk.IconTheme.get_default()
        if os.path.exists(icon):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, size, size)
        elif icon_theme.has_icon(icon):
            pixbuf = icon_theme.load_icon(icon, size, 
                                          Gtk.IconLookupFlags.USE_BUILTIN)
        else:
            pixbuf = icon_theme.load_icon(Gtk.STOCK_MISSING_IMAGE, size, 
                                          Gtk.IconLookupFlags.USE_BUILTIN)
        
        return pixbuf
