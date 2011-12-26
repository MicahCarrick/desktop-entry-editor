SUBDIRS = ui icons

desktopdir = $(datadir)/applications
desktop_in_files=desktop-entry-editor.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)
@INTLTOOL_DESKTOP_RULE@

#gsettings_ENUM_NAMESPACE = apps.desktop-entry-editor
gsettings_SCHEMAS = apps.desktop-entry-editor.gschema.xml
@GSETTINGS_RULES@

EXTRA_DIST = \
	$(desktop_in_files) \
	org.gnome.gedit.gschema.xml.in.in

CLEANFILES = \
	$(desktop_DATA)	\
	$(gsettings_SCHEMAS)	
	
DISTCLEANFILES = \
	$(desktop_DATA) \
	$(gsettings_SCHEMAS)
