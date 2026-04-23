def setUp(self):
        # Save up the number of connected signals so that we can check at the
        # end that all the signals we register get properly unregistered
        # (#9989)
        self.pre_signals = (
            len(signals.pre_save.receivers),
            len(signals.post_save.receivers),
            len(signals.pre_delete.receivers),
            len(signals.post_delete.receivers),
        )