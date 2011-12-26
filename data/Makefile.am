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
	apps.desktop-entry-editor.gschema.xml

CLEANFILES = \
	$(desktop_DATA)	
	
DISTCLEANFILES = \
	$(desktop_DATA) 

install-data-hook:
	update-desktop-database $(datadir)/applications || :
