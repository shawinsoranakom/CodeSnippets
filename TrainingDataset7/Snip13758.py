def _exc_info_to_string(self, err, test):
        # Make this method no-op. It only powers the default unittest behavior
        # for recording errors, but this class pickles errors into 'events'
        # instead.
        return ""