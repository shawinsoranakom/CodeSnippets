def winconfig_event(self, event):
        if self.is_configuring:
            # Avoid running on recursive <Configure> callback invocations.
            return

        self.is_configuring = True
        if not self.is_active():
            return

        # Since the <Configure> event may occur after the completion window is gone,
        # catch potential TclError exceptions when accessing acw.  See: bpo-41611.
        try:
            # Position the completion list window
            text = self.widget
            text.see(self.startindex)
            x, y, cx, cy = text.bbox(self.startindex)
            acw = self.autocompletewindow
            if platform.system().startswith('Windows'):
                # On Windows an update() call is needed for the completion
                # list window to be created, so that we can fetch its width
                # and height.  However, this is not needed on other platforms
                # (tested on Ubuntu and macOS) but at one point began
                # causing freezes on macOS.  See issues 37849 and 41611.
                acw.update()
            acw_width, acw_height = acw.winfo_width(), acw.winfo_height()
            text_width, text_height = text.winfo_width(), text.winfo_height()
            new_x = text.winfo_rootx() + min(x, max(0, text_width - acw_width))
            new_y = text.winfo_rooty() + y
            if (text_height - (y + cy) >= acw_height # enough height below
                or y < acw_height): # not enough height above
                # place acw below current line
                new_y += cy
            else:
                # place acw above current line
                new_y -= acw_height
            acw.wm_geometry("+%d+%d" % (new_x, new_y))
            acw.deiconify()
            acw.update_idletasks()
        except TclError:
            pass

        if platform.system().startswith('Windows'):
            # See issue 15786.  When on Windows platform, Tk will misbehave
            # to call winconfig_event multiple times, we need to prevent this,
            # otherwise mouse button double click will not be able to used.
            try:
                acw.unbind(WINCONFIG_SEQUENCE, self.winconfigid)
            except TclError:
                pass
            self.winconfigid = None

        self.is_configuring = False