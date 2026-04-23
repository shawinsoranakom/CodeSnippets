def log(self, msg, level=None):
        """
        Log the message at the given logging level (the default is INFO).

        If a logger isn't set, the message is instead printed to the console,
        respecting the configured verbosity. A verbosity of 0 prints no output,
        a verbosity of 1 prints INFO and above, and a verbosity of 2 or higher
        prints all levels.
        """
        if level is None:
            level = logging.INFO
        if self.logger is None:
            if self.verbosity <= 0 or (self.verbosity == 1 and level < logging.INFO):
                return
            print(msg)
        else:
            self.logger.log(level, msg)