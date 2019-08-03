import os
import glob
import sys
import logging
import subprocess
import tempfile

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Pango', '1.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import GObject, Gio
from gi.repository import Pango
from gi.repository import Gdk, GdkPixbuf, Gtk, GLib
from gi.repository import GtkSource

from dee.entry import Entry, get_icon_pixbuf
from dee.exceptiondialog import ExceptionDialog
from xdg.Exceptions import  ParsingError, ValidationError
from xdg.BaseDirectory import xdg_data_dirs, xdg_data_home


SETTINGS_SCHEMA = "apps.desktop-entry-editor"

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

class Application(object):

    APP_NAME = "Desktop Entry Editor"
    APP_DESCRIPTION = "A Desktop Entry editor based on freedesktop.org specifications."

    STATE_NORMAL = 0
    STATE_LOADING = 1
    BASIC_TAB = 0
    ADVANCED_TAB = 1
    SOURCE_TAB = 2

    # http://standards.freedesktop.org/desktop-entry-spec/latest/ar01s05.html
    ALL_KEYS = (
        ('Type', 'This specification defines 3 types of desktop entries: Application (type 1), Link (type 2) and Directory (type 3). To allow the addition of new types in the future, implementations should ignore desktop entries with an unknown type.', str),
        ('Version', 'Version of the Desktop Entry Specification that the desktop entry conforms with. Entries that confirm with this version of the specification should use 1.0. Note that the version field is not required to be present.', str),
        ('Name', 'Specific name of the application, for example "Mozilla".', str),
        ('GenericName', 'Generic name of the application, for example "Web Browser".', str),
        ('NoDisplay', 'NoDisplay means "this application exists, but don\'t display it in the menus". This can be useful to e.g. associate this application with MIME types, so that it gets launched from a file manager (or other apps), without having a menu entry for it (there are tons of good reasons for this, including e.g. the netscape -remote, or kfmclient openURL kind of stuff).', bool),
        ('Comment', 'Tooltip for the entry, for example "View sites on the Internet". The value should not be redundant with the values of Name and GenericName.', str),
        ('Icon','Icon to display in file manager, menus, etc. If the name is an absolute path, the given file will be used. If the name is not an absolute path, the algorithm described in the Icon Theme Specification will be used to locate the icon.', str),
        ('Hidden', 'Hidden should have been called Deleted. It means the user deleted (at his level) something that was present (at an upper level, e.g. in the system dirs). It\'s strictly equivalent to the .desktop file not existing at all, as far as that user is concerned. This can also be used to "uninstall" existing files (e.g. due to a renaming) - by letting make install install a file with Hidden=true in it.', bool),
        ('OnlyShowIn','A list of strings identifying the environments that should display/not display a given desktop entry. Only one of these keys, either OnlyShowIn or NotShowIn, may appear in a group (for possible values see the Desktop Menu Specification).', str),
        ('NotShowIn','A list of strings identifying the environments that should display/not display a given desktop entry. Only one of these keys, either OnlyShowIn or NotShowIn, may appear in a group (for possible values see the Desktop Menu Specification).', str),
        ('TryExec','Path to an executable file on disk used to determine if the program is actually installed. If the path is not an absolute path, the file is looked up in the $PATH environment variable. If the file is not present or if it is not executable, the entry may be ignored (not be used in menus, for example).',str),
        ('Exec','Program to execute, possibly with arguments.',str),
        ('Path','If entry is of type Application, the working directory to run the program in.',str),
        ('Terminal','Whether the program runs in a terminal window.',bool),
        ('MimeType','The MIME type(s) supported by this application.',str),
        ('Categories','Categories in which the entry should be shown in a menu (for possible values see the Desktop Menu Specification).',str),
        ('StartupNotify','If true, it is KNOWN that the application will send a "remove" message when started with the DESKTOP_STARTUP_ID environment variable set. If false, it is KNOWN that the application does not work with startup notification at all (does not shown any window, breaks even when using StartupWMClass, etc.). If absent, a reasonable handling is up to implementations (assuming false, using StartupWMClass, etc.). (See the Startup Notification Protocol Specification for more details).',bool),
        ('StartupWMClass','If specified, it is known that the application will map at least one window with the given string as its WM class or WM name hint (see the Startup Notification Protocol Specification for more details).',str),
        ('URL','If entry is Link type, the URL to access.',str)
    )

    def close_file(self):
        """
        Close the currently open desktop entry file.
        """
        self._entry = None
        self._load_desktop_entry_ui()
        # TODO deselect tree view

    def _ensure_user_dir(self):
        """
        Ensures the user's applications directory exists.
        """
        path = os.path.join(xdg_data_home, "applications")
        if not os.path.exists(path):
            os.makedirs(path)

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

    def overwrite_existing_file_dialog(self, filename):
        """
        Prompt the user to overwrite an existing file.
        """
        if os.path.exists(filename):
            message = "A file named %s already exists.\nDo you want to replace it?" \
                % os.path.basename(filename)
            dialog = Gtk.MessageDialog(self.window,
                                       Gtk.DialogFlags.MODAL |
                                       Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                       Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO,
                                       message)
            dialog.set_title('Overwrite Existing File?')
            r = dialog.run()
            dialog.destroy()

            if r == Gtk.ResponseType.YES:
                return True
            else:
                return False

        return True

    def _get_app_icon_pixbuf(self, size=None):
        """
        Get a new GdkPixbuf for the app's main icon rendered at size.
        """
        pixbuf_file = os.path.join(self.ICON_DIR, "scalable", "desktop-entry-editor.svg")
        if not os.path.exists(pixbuf_file):
            return None
        if size:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(pixbuf_file, size, size, True)
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(pixbuf_file)
        return pixbuf

    def info_dialog(self, message, title="Information"):
        """ Display a very basic info dialog. """
        dialog = Gtk.MessageDialog(self.window,
                                   Gtk.DialogFlags.MODAL |
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.INFO, Gtk.ButtonsType.OK,
                                   message)
        dialog.set_title(title)
        dialog.run()
        dialog.destroy()

    def __init__(self, package, version, data_dir, debug=False):
        """
        Build UI from Glade XML file found in self.DATA_DIR.
        """
        if debug:
            logger.setLevel(logging.DEBUG)

        self.PACKAGE = package
        self.VERSION = version
        self.DATA_DIR = data_dir
        self.UI_DIR = os.path.join(data_dir, 'ui')

        logger.debug("-"*60)
        logger.debug("  %s %s" % (self.PACKAGE, self.VERSION))
        logger.debug("  DATA DIR: " + self.DATA_DIR)
        logger.debug("-"*60)

        builder = Gtk.Builder()
        try:
            builder.add_from_file(os.path.join(self.UI_DIR, "main_window.ui"))
        except Exception as e:
            logger.debug(self.UI_DIR)
            sys.exit(str(e))
        self.window = builder.get_object("main_window")
        self.window.set_icon_name(self.PACKAGE)
        self._notebook = builder.get_object("notebook")
        self._statusbar = builder.get_object("statusbar")
        self._statusbar_ctx = self._statusbar.get_context_id("Selected entry.")
        self._init_settings()
        self._init_menu_and_toolbar(builder)
        self._init_treeview(builder)
        self._init_basic_tab(builder)
        self._init_advanced_tab(builder)
        self._init_source_tab(builder)

        self._type_application_widgets = (
            builder.get_object("terminal_label"),
            builder.get_object("terminal_checkbutton"),
            builder.get_object("exec_label"),
            builder.get_object("exec_entry"),
            builder.get_object("exec_open_button"),
        )
        self._type_directory_widgets = (

        )
        self._type_link_widgets = (
            builder.get_object("url_label"),
            builder.get_object("url_entry"),
        )

        builder.connect_signals(self)
        self._state = self.STATE_NORMAL
        self.close_file()

    def _init_settings(self):
        """
        Initialize a GSettings object and connect callbacks.
        """
        self._settings = Gio.Settings.new(SETTINGS_SCHEMA)
        self._settings.connect("changed::show-read-only-files",
                               lambda settings,key: self._load_treeview())

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
        # temporary until code for editing source is fixed
        self._sourceview.set_editable(False)


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
                              GObject.TYPE_STRING,      # tooltip
                              GObject.TYPE_STRING)      # markup
        model.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        self._treeview.set_model(model)
        self._treeview.set_headers_visible(False)

        column = Gtk.TreeViewColumn("Launchers")
        cell = Gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", 0)
        cell = Gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "markup", 4)
        self._treeview.append_column(column)

        self._missing_pixbuf = self.window.render_icon_pixbuf(Gtk.STOCK_MISSING_IMAGE,
                                                              Gtk.IconSize.MENU)

    def _init_advanced_tab(self, builder):
        """
        Initialize the advanced tab with a treeview of key/values.
        """
        self._advanced_treeview = builder.get_object("advanced_treeview")
        treeview = self._advanced_treeview
        model = Gtk.ListStore(GObject.TYPE_STRING,      # key
                              GObject.TYPE_STRING,      # value (as string)
                              GObject.TYPE_STRING)      # tooltip
        model.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        treeview.set_model(model)
        treeview.set_headers_visible(True)

        column = Gtk.TreeViewColumn("Key")
        cell = Gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        treeview.append_column(column)

        column = Gtk.TreeViewColumn("Value")
        cell = Gtk.CellRendererText()
        cell.set_property("editable", True)
        cell.connect("edited", self.on_advanced_treeview_edited, treeview)
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 1)
        treeview.append_column(column)

    def _init_basic_tab(self, builder):
        """
        Initialize the the "Basic" tab with the minimum fields for a launcher.
        """
        self._type_combo = builder.get_object("type_combo")
        self._name_entry = builder.get_object("name_entry")
        self._icon_entry = builder.get_object("icon_entry")
        self._exec_entry = builder.get_object("exec_entry")
        self._url_entry = builder.get_object("url_entry")
        self._terminal_checkbutton = builder.get_object("terminal_checkbutton")

        # populate type combo box
        model = Gtk.ListStore(GObject.TYPE_STRING)
        model.append(("Application",))
        model.append(("Directory",))
        model.append(("Link",))

        cell = Gtk.CellRendererText()
        self._type_combo.pack_start(cell, True)
        self._type_combo.add_attribute(cell, "text", 0)

        self._type_combo.set_model(model)
        self._type_combo.set_id_column(0)
        self._type_combo.set_active_id("Application")

    def _init_menu_and_toolbar(self, builder):
        """
        Load the menu and toolbar from the UI definitions file.
        """
        manager = Gtk.UIManager()
        accelgroup = manager.get_accel_group()
        self.window.add_accel_group(accelgroup)

        # global actions are always sensitive
        self._app_actions = Gtk.ActionGroup("AppActions")
        self._app_actions.add_actions([
            ('File', None, '_File', None, None, None),
            ('View', None, '_View', None, None, None),
            ('Tools', None, '_Tools', None, None, None),
            ('Help', None, '_Help', None, None, None),
            ('New', Gtk.STOCK_NEW, None, None, "Create new",
                self.on_file_new_activate),
            ('Open', Gtk.STOCK_OPEN, None, None, "Open file",
                self.on_file_open_activate),
            ('Quit', Gtk.STOCK_QUIT, None, None, None,
                self.quit),
            ('Refresh', Gtk.STOCK_REFRESH, None, None, "Refresh list",
                self.on_view_refresh_activate),
            ('About', Gtk.STOCK_ABOUT, None, None, None,
                self.on_help_about_activate),
        ])
        self._app_actions.add_toggle_actions([
            ('ViewReadOnly', None, "Show _read-only files", None, None,
                self.on_view_read_only_toggled,
                self._settings.get_boolean("show-read-only-files")),
            #('ViewToolbar', None, "_Toolbar", None, None,
            #    self.on_view_toolbar_toggled, False),
        ])

        self._save_actions = Gtk.ActionGroup("SaveActions")
        self._save_actions.add_actions([
            ('Save', Gtk.STOCK_SAVE, None, None, "Save current file",
                self.on_file_save_activate),
        ])
        self._save_actions.set_sensitive(False)

        self._open_actions = Gtk.ActionGroup("OpenActions")
        self._open_actions.add_actions([
            ('SaveAs', Gtk.STOCK_SAVE_AS, None, None, None,
                self.on_file_save_as_activate),
            ('Close', Gtk.STOCK_CLOSE, None, None, None,
                self.on_file_close_activate),
            ('Validate', None, "Validate", None, None,
                self.on_tools_validate_activate),
        ])

        manager.insert_action_group(self._app_actions)
        manager.insert_action_group(self._save_actions)
        manager.insert_action_group(self._open_actions)

        ui_file = os.path.join(self.UI_DIR, 'menu_toolbar.ui')
        manager.add_ui_from_file(ui_file)
        menu = manager.get_widget('ui/MenuBar')
        toolbar = manager.get_widget('ui/MainToolbar')

        self._ui_manager = manager

        # pack into main interface box
        box = builder.get_object("main_box")
        box.pack_start(toolbar, False, True, 0)
        box.pack_start(menu, False, True, 0)
        box.reorder_child(menu, 0)
        box.reorder_child(toolbar, 1)

    def install_exception_hook(self):
        """
        Install an exception hook to display unhandled exceptions in a dialog
        and allow the user to submit a bug report.
        """
        def new_hook(etype, evalue, etraceback):
            if etype not in (KeyboardInterrupt, SystemExit):
                url = "https://github.com/MicahCarrick/desktop-entry-editor/issues/new" \
                      "?title=Bug Report: %s" \
                      "&body=Please paste your bug report here with CTRL+V.%%0A" \
                      % (evalue)
                dialog = ExceptionDialog(parent=self.window,
                                         bug_report_url=url)
                dialog.set_markup("<b>Fatal Error</b>\n\n"
                                  "An unhandled exception has occured and the "
                                  "program will now exit.\n"
                                  "A detailed report has been copied to your "
                                  "clipboard.\nUse the link below to submit a "
                                  "bug report.")
                dialog.run(etype, evalue, etraceback)
                dialog.destroy()
            if Gtk.main_level():
                Gtk.main_quit()
        old_hook = sys.excepthook
        sys.excepthook = new_hook
        return old_hook

    def _load_desktop_entry_ui(self):
        """
        Load the current Entry into the various widgets of the GUI.
        """
        self._state = self.STATE_LOADING
        entry = self._entry
        self._update_ui()
        if not entry:
            # clear all
            self._status_pop()
            self._sourceview.get_buffer().set_text("")
            self._type_combo.set_active_id("Application")
            self._name_entry.set_text("")
            self._icon_entry.set_text("")
            self._exec_entry.set_text("")
            self._terminal_checkbutton.set_active(False)
            self._open_actions.set_sensitive(False)
            self._notebook.set_sensitive(False)
            self._state = self.STATE_NORMAL
            return

        # statusbar
        self._status_push(entry.filename)


        # populate basic tab
        self._update_basic_tab()

        # populate advanced tab

        # load file into source view
        self._update_source_tab()

        self._open_actions.set_sensitive(True)
        self._notebook.set_sensitive(True)
        self._state = self.STATE_NORMAL

    def _load_treeview(self):
        """
        Load the treeview with the .desktop entries found at path.
        """

        self._treeview.get_bin_window().set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))
        self._status_push("Loading...")
        while Gtk.events_pending():
            Gtk.main_iteration()

        model = self._treeview.get_model()
        model.clear()
        #
        show_ro = self._settings.get_boolean('show-read-only-files')
        for path in xdg_data_dirs:
            path = os.path.join(path, "applications")
            logger.debug("Loading desktop entries from %s" % path)
            for desktop_file in glob.glob(os.path.join(path, "*.desktop")):
                #logger.debug(desktop_file)
                try:
                    entry = Entry(desktop_file)
                except ParsingError as e:
                    logger.warn(e)
                    continue # skip entries with parse errors

                pixbuf = entry.getIconPixbuf(16)

                if entry.getGenericName():
                    tooltip = entry.getGenericName()
                else:
                    tooltip = entry.getName()
                tooltip = GLib.markup_escape_text(tooltip)

                markup = GLib.markup_escape_text(entry.getName())
                if entry.isReadOnly():
                    if show_ro:
                        markup = "<span color='#888888'>%s</span>" % markup
                    else:
                        continue # skip read-only per settings

                model.append((pixbuf, entry.getName(), desktop_file, tooltip, markup,))
        self._treeview.get_bin_window().set_cursor(None)
        self._status_pop()

    def new_file(self):
        """
        Create a new, empty desktop entry.
        """
        old_entry = self._entry
        self._entry = Entry()
        filename = self.save_dialog()
        if filename:
            if filename[-8:] != ".desktop":
                filename = filename + ".desktop"
            self._entry.new(filename)
            self._entry.set("Name", "Untitled")
            logger.debug(self._entry.getName())
            self.save_file(filename)
            return
        self._entry = old_entry

    def on_advanced_treeview_edited(self, cell, path, new_text, treeview):
        """
        Update the treeview and the entry when the treeview values are edited.
        """
        model = treeview.get_model()
        key = model[path][0]
        model[path][1] = new_text
        self._ui_value_changed(key, new_text)

    def on_type_combo_changed(self, combo, data=None):
        type_str = combo.get_model()[combo.get_active()][0]
        self._ui_value_changed("Type", type_str)
        if self._entry:
            self._update_basic_tab()

    def on_exec_entry_changed(self, entry, data=None):
        self._ui_value_changed("Exec", entry.get_text())

    def on_exec_entry_icon_press(self, entry, icon_pos, event, data=None):
        """
        Execute the command when the user presses the icon in the entry.
        """
        # TODO async? Wait for retval?
        if not self._entry:
            return
        retval = subprocess.call(self._entry.getExec(), shell=True)
        logger.debug("Exited with code " + str(retval))

    def on_file_close_activate(self, action, data=None):
        self.close_file()

    def on_file_new_activate(self, action, data=None):
        self.new_file()

    def on_file_open_activate(self, action, data=None):
        filename = self.open_dialog()
        if filename:
            self.open_file(filename)

    def on_file_save_activate(self, action, data=None):
        self.save_file(self._entry.filename)

    def on_file_save_as_activate(self, action, data=None):
        filename = self.save_dialog()
        if filename:
            self.save_file(filename)

    def on_help_about_activate(self, action, data=None):
        """
        Show the about dialog.
        """
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self.window)
        dialog.set_modal(True)
        dialog.set_authors(("Micah Carrick <micah@quixotix.com>",))
        dialog.set_copyright("Copyright (c) 2011, Quixotix Software LLC")
        dialog.set_logo_icon_name(self.PACKAGE)
        dialog.set_program_name(self.APP_NAME)
        dialog.set_version(self.VERSION)
        dialog.set_comments(self.APP_DESCRIPTION)
        dialog.run()
        dialog.destroy()

    def on_icon_entry_changed(self, entry, data=None):
        """
        Update the primary icon as the user enters text.
        """
        icon = entry.get_text()
        self._ui_value_changed("Icon", icon)

        entry.set_property("primary-icon-pixbuf", get_icon_pixbuf(icon, 16))

    def on_icon_entry_icon_press(self, entry, icon_pos, event, data=None):
        """
        Show the icon preview dialog if the user clicks the icon entry's primary
        icon.
        """
        if not self._entry:
            return
        builder = Gtk.Builder()
        try:
            builder.add_from_file(os.path.join(self.UI_DIR, "icon_preview_dialog.ui"))
        except Exception as e:
            sys.exit(str(e))
        dialog = builder.get_object("icon_preview_dialog")
        label = builder.get_object("icon_name_label")
        label.set_markup("<b>%s</b>" % GLib.markup_escape_text(self._entry.getIcon()))
        button = builder.get_object("close_button")
        button.connect("clicked", lambda button,dialog: dialog.destroy(), dialog)
        dialog.set_transient_for(self.window)

        for size in (16,24,32,48,64,128):
            image = builder.get_object("image_%s" % str(size))
            if image:
                image.set_from_pixbuf(self._entry.getIconPixbuf(size))
        dialog.show()

    def on_save_button_clicked(self, button, data=None):
        self.save_file(self._entry.filename)

    def on_terminal_button_toggled(self, button, data=None):
        self._ui_value_changed("Terminal", str(button.get_active()).lower())

    def on_tools_validate_activate(self, action, data=None):
        """
        Run the validate() method on the entry and show the results in a Gtk
        dialog.
        """
        try:
            self._entry.validate()
        except ValidationError as e:
            self.error_dialog(e)
            return
        self.info_dialog("%s is valid." % os.path.basename(self._entry.filename),
                         "Validation")

    def on_treeview_button_press_event(self, treeview, event, data=None):
        # if user needs to save...
            # return True
        return False

    def on_main_window_map_event(self, window, event, data=None):
        #while Gtk.events_pending():
        #    Gtk.main_iteration()
        pass

    def on_main_window_show(self, window, data=None):
        self._ensure_user_dir()
        self._load_treeview()
        pass

    def on_name_entry_changed(self, entry, data=None):
        self._ui_value_changed("Name", entry.get_text())

    def on_notebook_switch_page(self, notebook, page, data=None):
        index = self._notebook.get_current_page()
        if index == self.SOURCE_TAB:
            self._update_source_tab()
        elif index == self.ADVANCED_TAB:
            self._update_advanced_tab()
        else:
            self._update_basic_tab()

    def on_treeview_selection_changed(self, selection, data=None):
        """
        Change the currently selected desktop entry.
        """
        model, iter = selection.get_selected()
        if model and iter:
            self.open_file(model.get_value(iter, 2))

    def on_url_entry_changed(self, entry, data=None):
        self._ui_value_changed("URL", entry.get_text())

    def on_url_entry_icon_press(self, entry, icon_pos, event, data=None):
        if not self._entry:
            return
        subprocess.call(["xdg-open", self._entry.getURL()])

    def on_view_read_only_toggled(self, action, data=None):
        self._settings.set_boolean("show-read-only-files",
                                    action.get_active())

    def on_view_refresh_activate(self, action, data=None):
        self._load_treeview()

    def on_view_toolbar_toggled(self, action, data=None):
        # TODO
        raise Exception("Testing")

    def open_dialog(self):
        """
        Return a user-selected save filename or None if the user cancels.
        """
        filename = None
        chooser = Gtk.FileChooserDialog("Open File...", self.window,
                                        Gtk.FileChooserAction.OPEN,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                         Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        for path in xdg_data_dirs:
            path = os.path.join(path, "applications")
            if os.path.exists(path) and os.access(path, os.W_OK):
                chooser.set_current_folder(path)
                break
        filter = Gtk.FileFilter()
        filter.add_pattern("*.desktop")
        filter.add_pattern("*.directory")
        chooser.set_filter(filter)

        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
        chooser.destroy()
        return filename

    def open_file(self, desktop_file):
        """
        Open the specified desktop file.
        """
        # TODO make sure this desktop file is selected in the list
        try:
            self._entry = Entry(desktop_file)
        except ParsingError as e:
            self.error_dialog(e)
            return

        self._load_desktop_entry_ui()
        # validate in save
        """
        try:
            entry.validate()
        except ValidationError, e:
            self.error_dialog(e)
            return
        """

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

    def save_dialog(self):
        """
        Return a user-selected save filename or None if the user cancels.
        """
        filename = None

        chooser = Gtk.FileChooserDialog("Save File...", self.window,
                                        Gtk.FileChooserAction.SAVE,
                                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                         Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        if self._entry and self._entry.filename:
            chooser.set_filename(self._entry.filename)
        else:
            for path in xdg_data_dirs:
                path = os.path.join(path, "applications")
                if os.path.exists(path) and os.access(path, os.W_OK):
                    chooser.set_current_folder(path)
                    break

        response = chooser.run()
        if response == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
        chooser.destroy()
        if filename:
            if not self.overwrite_existing_file_dialog(filename):
                filename = None
        return filename

    def save_file(self, filename):
        # TODO confirm user wants to save if the file is invalid
        self._entry.write(filename)
        self._load_treeview()
        self.set_modified(False)
        self._load_desktop_entry_ui()

    def set_modified(self, modified=True):
        """
        Set the modified flag on the entry and update the titlebar
        """
        self._entry.is_modified = modified
        self._update_ui()

    def _status_pop(self):
        """
        Pop the last status message off the statusbar.
        """
        self._statusbar.pop(self._statusbar_ctx)

    def _status_push(self, status):
        """
        Push a status message into the statusbar.
        """
        self._statusbar.push(self._statusbar_ctx, status)

    def _ui_value_changed(self, key, value):
        """
        Generic method to handle user changes to the Entry via the GUI.
        """
        if self._state == self.STATE_NORMAL:
            self.set_modified(True)
        else:
            return # do not continue if we're loading UI

        if not value:
            self._entry.removeKey(key)
        else:
            self._entry.set(key, value)

    def _update_advanced_tab(self):
        """
        Update the advanced tab based on the current state of the Entry.
        """
        model = self._advanced_treeview.get_model()
        model.clear()
        for key, tooltip, t in self.ALL_KEYS:
            try:
                value = str(self._entry.get(key))
            except:
                value = None
            tooltip = GLib.markup_escape_text(tooltip)
            model.append((key, value, tooltip,))

    def _update_basic_tab(self):
        """
        Update the basic tab based on the current state of the Entry.
        """
        entry = self._entry

        # hide widgets based on type
        [widget.set_visible(False) for widget in self._type_link_widgets]
        [widget.set_visible(False) for widget in self._type_directory_widgets]
        [widget.set_visible(False) for widget in self._type_application_widgets]
        entry_type = entry.getType()
        if entry_type == "Directory":
            [widget.set_visible(True) for widget in self._type_directory_widgets]
        elif entry_type == "Link":
            [widget.set_visible(True) for widget in self._type_link_widgets]
        else:
            [widget.set_visible(True) for widget in self._type_application_widgets]

        self._type_combo.set_active_id(entry.getType())
        self._name_entry.set_text(entry.getName())
        self._icon_entry.set_text(entry.getIcon())
        self._exec_entry.set_text(entry.getExec())
        self._terminal_checkbutton.set_active(entry.getTerminal())
        self._url_entry.set_text(entry.getURL())


    def _update_source_tab(self):
        """
        Update the source tab with the contents of what the .desktop file would
        look like based on the current, possibly unsaved entry.
        """
        # temporarily change entry filename to a temp file to write it's output
        entry = self._entry
        original_filename = self._entry.filename
        (fd, filename) = tempfile.mkstemp(suffix=".desktop")
        entry.write(filename)

        # load temp file into sourceview
        #self._sourceview.set_editable(False)
        buffer = self._sourceview.get_buffer()
        with open(entry.filename, 'r') as f:
            buffer.set_text(f.read())
        f.closed
        #self._sourceview.set_editable(True)

        # clean up
        if fd:
            os.close(fd)
        if filename:
            os.remove(filename)
        entry.filename = original_filename

    def _update_ui(self):
        """
        Update the UI to reflect the state of the the current Entry.
        """
        entry = self._entry

        # titlebar
        if not entry:
            self.window.set_title(self.APP_NAME)
        else:
            read_only = modified_indicator = ""
            if entry.isReadOnly():
                read_only = "(read-only)"
            if entry.is_modified:
                modified_indicator = "*"
            self.window.set_title("%s%s %s - %s" % (modified_indicator,
                                                    os.path.basename(entry.filename),
                                                    read_only,
                                                    self.APP_NAME))
        # save buttons
        if entry and entry.isModified() and not entry.isReadOnly():
            self._save_actions.set_sensitive(True)
        else:
            self._save_actions.set_sensitive(False)
