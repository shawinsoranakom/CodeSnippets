def saved_change_hook(self):
        short = self.short_title()
        long = self.long_title()
        _py_version = ' (%s)' % platform.python_version()
        if short and long and not macosx.isCocoaTk():
            # Don't use both values on macOS because
            # that doesn't match platform conventions.
            title = short + " - " + long + _py_version
        elif short:
            if short == "IDLE Shell":
                title = short + " " +  platform.python_version()
            else:
                title = short + _py_version
        elif long:
            title = long
        else:
            title = "untitled"
        icon = short or long or title
        if not self.get_saved():
            title = "*%s*" % title
            icon = "*%s" % icon
        self.top.wm_title(title)
        self.top.wm_iconname(icon)

        if macosx.isCocoaTk():
            # Add a proxy icon to the window title
            self.top.wm_attributes("-titlepath", long)

            # Maintain the modification status for the window
            self.top.wm_attributes("-modified", not self.get_saved())