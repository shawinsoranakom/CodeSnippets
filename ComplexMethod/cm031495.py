def recolorize(self):
        """Timer event (every 1ms) to colorize text.

        Colorizing is only attempted when the text widget exists,
        when colorizing is toggled on, and when the colorizing
        process is not already running.

        After colorizing is complete, some cleanup is done to
        make sure that all the text has been colorized.
        """
        self.after_id = None
        if not self.delegate:
            if DEBUG: print("no delegate")
            return
        if not self.allow_colorizing:
            if DEBUG: print("auto colorizing is off")
            return
        if self.colorizing:
            if DEBUG: print("already colorizing")
            return
        try:
            self.stop_colorizing = False
            self.colorizing = True
            if DEBUG: print("colorizing...")
            t0 = time.perf_counter()
            self.recolorize_main()
            t1 = time.perf_counter()
            if DEBUG: print("%.3f seconds" % (t1-t0))
        finally:
            self.colorizing = False
        if self.allow_colorizing and self.tag_nextrange("TODO", "1.0"):
            if DEBUG: print("reschedule colorizing")
            self.after_id = self.after(1, self.recolorize)