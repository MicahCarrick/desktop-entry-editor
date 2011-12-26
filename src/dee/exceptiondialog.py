import platform
import traceback
from gi.repository import Gtk, Gdk
    
class ExceptionDialog(Gtk.MessageDialog):
    _bug_report_url = None
    def __init__(self, parent=None, bug_report_url=None):
        Gtk.MessageDialog.__init__(self, parent, Gtk.DialogFlags.MODAL | 
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.ERROR, Gtk.ButtonsType.OK)
        self.set_title("Exception")
        self._textview = Gtk.TextView()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.add(self._textview)
        scrolled.set_min_content_height(150)
        expander = Gtk.Expander.new_with_mnemonic("Details")
        expander.add(scrolled)
        button = Gtk.LinkButton.new_with_label(bug_report_url,
                                                    "Submit a Bug Report")
        self.vbox.pack_start(button, False, False, 0)
        button.set_hexpand(False)
        button.set_halign(Gtk.Align.CENTER)
        self.vbox.pack_start(expander, True, True, 0)
        self.vbox.show_all()
       
    def run(self, etype, evalue, etraceback):
        text = "".join(traceback.format_exception(etype, evalue, etraceback))
        gtk_version = "%s.%s.%s" % (Gtk.get_major_version(),
                                    Gtk.get_minor_version(),
                                    Gtk.get_micro_version())
        info = "\n\nPlatform: %s\nPython: %s\nGTK+:%s\n\n" % (platform.platform(),
                                                              platform.python_version(),
                                                              gtk_version)
        self._textview.get_buffer().set_text(text)
        clipboard = Gtk.Clipboard.get_for_display(Gdk.Display.get_default(), 
                                                  Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text+info, -1)
        Gtk.MessageDialog.run(self)
