import os
import glob
import sys
import logging
import subprocess
import shlex
from gi.repository import GObject, Gio, Gdk, GdkPixbuf, Gtk, Pango
from gi.repository import GtkSource
from dee.entry import Entry
from xdg.DesktopEntry import  ParsingError, ValidationError

from xdg.BaseDirectory import xdg_data_dirs

APP_NAME = "Desktop Entry Editor"
DATA_DIR = "data"
# XDG_DATA_DIR
SETTINGS_SCHEMA = "apps.desktop-entry-editor"

logging.basicConfig()
LOG_LEVEL = logging.DEBUG
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

class Application(object):
    
    DESKTOP_ENTRY_DIRS = (
        os.path.join(os.path.expanduser("~"), ".local", "share", "applications"),
        os.path.join("usr", "share", "applications"),
        os.path.join("usr", "local", "share", "applications"),
    )
    
    def error_dialog(self, message):
        """ Display a very basic error dialog. """
        logger.warn(message)
        dialog = Gtk.MessageDialog(self.window,
                                   Gtk.DialogFlags.MODAL | 
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, 
                                   message)
        dialog.set_title("Error")
        dialog.run()
        dialog.destroy()
        
    def __init__(self):
        """
        Build UI from Glade XML file found in DATA_DIR.
        """
        self._settings = Gio.Settings.new(SETTINGS_SCHEMA)
        builder = Gtk.Builder()
        try:
            builder.add_from_file(os.path.join(DATA_DIR, "main_window.ui"))
        except Exception as e:
            sys.exit("Failed to load UI file: %s." % str(e))
        self.window = builder.get_object("main_window")
        self.window.set_icon_name(Gtk.STOCK_EXECUTE)
        #paned = builder.get_object("paned")
        #paned.set_position(self._settings.get_int("paned-position"))
        self._statusbar = builder.get_object("statusbar")
        self._statusbar_ctx = self._statusbar.get_context_id("Selected entry.")
        self._folder_select = builder.get_object("folder_select")
        self._init_treeview(builder)
        self._init_basic_tab(builder)
        self._init_source_tab(builder)
        
        builder.connect_signals(self)
        self._desktop_file = None
    
    def _init_source_tab(self, builder):
        """
        Initialize a GtkSourceView to show the desktop entry in the 'Source' tab
        """
        scrolled_window = builder.get_object("source_scrolled_window")
        # why do I have to explicity create the buffer?
        self._sourceview = GtkSource.View.new_with_buffer(GtkSource.Buffer())
        buffer = self._sourceview.get_buffer()
        scrolled_window.add(self._sourceview)
        self._sourceview.set_show_line_numbers(True)
        font_desc = Pango.FontDescription("monospace 10") # TODO configurable
        self._sourceview.modify_font(font_desc)
        manager = GtkSource.LanguageManager().get_default()
        language = manager.get_language("ini")
        buffer.set_language(language)
        scrolled_window.show_all()
        
        
    def _init_treeview(self, builder):
        """
        Initialize the tree view's model and columns.
        """
        self._treeview = builder.get_object("treeview")
        # why doesn't button-press-event work when defined in Glade?
        self._treeview.connect("button-press-event", self.on_treeview_button_press_event)
        model = Gtk.ListStore(GdkPixbuf.Pixbuf,         # icon
                              GObject.TYPE_STRING,      # name
                              GObject.TYPE_STRING,      # desktop entry file
                              GObject.TYPE_STRING)      # tooltip
        model.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        self._treeview.set_model(model)
        self._treeview.set_headers_visible(False)
        
        column = Gtk.TreeViewColumn("Launchers")
        cell = Gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", 0)
        cell = Gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 1)
        self._treeview.append_column(column)
        
        self._missing_pixbuf = self.window.render_icon_pixbuf(Gtk.STOCK_MISSING_IMAGE,
                                                              Gtk.IconSize.MENU)
    
    def _init_basic_tab(self, builder):
        """
        Initialize the combo box that holds the desktop entry type.
        """
        self._type_combo = builder.get_object("type_combo")
        self._name_entry = builder.get_object("name_entry")
        self._icon_entry = builder.get_object("icon_entry")
        self._exec_entry = builder.get_object("exec_entry")
        self._terminal_checkbutton = builder.get_object("terminal_checkbutton")
        
        # populate type combo box
        model = Gtk.ListStore(GObject.TYPE_STRING, GObject.TYPE_STRING)
        model.append((Gtk.STOCK_EXECUTE, "Application",))
        model.append((Gtk.STOCK_DIRECTORY, "Directory",))
        model.append(('web-browser', "Link",))
        # TODO: register a stock icon for link
        
        cell = Gtk.CellRendererPixbuf()
        self._type_combo.pack_start(cell, False)
        self._type_combo.add_attribute(cell, "icon-name", 0)
        cell = Gtk.CellRendererText()
        self._type_combo.pack_start(cell, True)
        self._type_combo.add_attribute(cell, "text", 1)
        
        self._type_combo.set_model(model)
        self._type_combo.set_id_column(1)
        self._type_combo.set_active_id("Application")
    
    def _load_treeview(self):
        """
        Load the treeview with the .desktop entries found at path.
        """
        self._treeview.set_sensitive(False)
        model = self._treeview.get_model()
        model.clear()
        for path in xdg_data_dirs:
            path = os.path.join(path, "applications")
            logger.debug("Loading desktop entries from %s" % path)
            for desktop_file in glob.glob(os.path.join(path, "*.desktop")):
                try:
                    entry = Entry(desktop_file)
                except ParsingError, e:
                    logger.warn(e)
                    continue # skip entries with parse errors

                pixbuf = entry.getIconPixbuf(16)

                if entry.getGenericName():
                    tooltip = entry.getGenericName()
                else:
                    tooltip = entry.getName()
                model.append((pixbuf, entry.getName(), desktop_file, tooltip,))
        self._treeview.set_sensitive(True)
        
    def on_exec_entry_icon_press(self, entry, icon_pos, event, data=None):
        """
        Execute the command when the user presses the icon in the entry.
        """
        # TODO async? Wait for retval?
        if not self._desktop_file:
            return
        entry = Entry(self._desktop_file)                
        retval = subprocess.call(entry.getExec(), shell=True)
        logger.debug("Exited with code " + str(retval))
        
    def on_folder_select_folder_changed(self, chooser, data=None):
        print "folder-changed"
        #self._load_treeview(chooser.get_filename())
    
    def on_icon_entry_changed(self, entry, data=None):
        """
        Update the primary icon as the user enters text.
        """
        icon = entry.get_text()
        icon_theme = Gtk.IconTheme.get_default()
        if os.path.exists(icon):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon, 16, 16)
            entry.set_property("primary-icon-pixbuf", pixbuf)
        elif icon_theme.has_icon(icon):
            #pixbuf = icon_theme.load_icon(icon, 16, Gtk.IconLookupFlags.USE_BUILTIN)
            entry.set_property("primary-icon-name", icon)
        else:
            entry.set_property("primary-icon-name", Gtk.STOCK_MISSING_IMAGE)

    def on_icon_entry_icon_press(self, entry, icon_pos, event, data=None):
        """
        Show the icon preview dialog if the user clicks the icon entry's primary
        icon.
        """
        entry = Entry(self._desktop_file)
        if not entry:
            return
        builder = Gtk.Builder()
        try:
            builder.add_from_file(os.path.join(DATA_DIR, "icon_preview_dialog.ui"))
        except Exception as e:
            sys.exit("Failed to load UI file: %s." % str(e))
        dialog = builder.get_object("icon_preview_dialog")
        label = builder.get_object("icon_name_label")
        label.set_markup("<b>%s</b>" % entry.getIcon())
        button = builder.get_object("close_button")
        button.connect("clicked", lambda button,dialog: dialog.destroy(), dialog)
        dialog.set_transient_for(self.window)
        
        for size in (16,24,32,48,64,128):
            image = builder.get_object("image_%s" % str(size))
            if image:
                image.set_from_pixbuf(entry.getIconPixbuf(size))
        dialog.show()
        
    def on_treeview_button_press_event(self, treeview, event, data=None):
        # if user needs to save...
            # return True
        return False
  
    def on_main_window_map_event(self, window, event, data=None):
        #while Gtk.events_pending():
        #    Gtk.main_iteration()
        pass
    
    def on_main_window_show(self, window, data=None):
        
        while Gtk.events_pending():
            Gtk.main_iteration()
        self._load_treeview()
        pass
        
    def on_treeview_selection_changed(self, selection, data=None):
        """
        Change the currently selected desktop entry.
        """
        model, iter = selection.get_selected()
        if model and iter:
            self.open_file(model.get_value(iter, 2))
    
    def open_file(self, desktop_file):
        """
        Open the specified desktop file.
        """
        # TODO make sure this desktop file is selected in the list
        self._desktop_file = desktop_file
        try:
            entry = Entry(desktop_file)
        except ParsingError, e:
            self.error_dialog(e)
            return
        # validate in save
        """
        try:
            entry.validate()
        except ValidationError, e:
            self.error_dialog(e)
            return
        """
        # statusbar
        self._statusbar.pop(self._statusbar_ctx)
        self._statusbar.push(self._statusbar_ctx, desktop_file)
        
        # window title
        self.window.set_title("%s - %s" % (os.path.basename(desktop_file), APP_NAME))
        
        # load file into source view
        self._sourceview.set_editable(False)
        buffer = self._sourceview.get_buffer()
        with open(desktop_file, 'r') as f:
            buffer.set_text(f.read())
        f.closed
        self._sourceview.set_editable(True)
        
        # populate basic tab
        if entry.getType():
            self._type_combo.set_active_id(entry.getType())
        if entry.getName():
            self._name_entry.set_text(entry.getName())
        self._icon_entry.set_text(entry.getIcon())
        if entry.getExec():
            self._exec_entry.set_text(entry.getExec())
 
        self._terminal_checkbutton.set_active(entry.getTerminal())
          
    def quit(self, widget=None, data=None):
        """
        Used as callback for both user quit (File > Quit) and window manager
        killing the window.
        """
        Gtk.main_quit()
        
    def run(self):
        """
        Show the main application window and enter GTK+ main loop.
        """
        self.window.show()
        Gtk.main()
        
    def set_folder(self, path):
        """
        By setting the folder on the GtkFileChooserButton, the treeview will
        be re-populated with contents of the currently selected folder.
        """
        self._folder_select.set_current_folder(path)
        
