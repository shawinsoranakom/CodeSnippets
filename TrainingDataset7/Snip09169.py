def _prepare_cursor(self, cursor):
        """
        Validate the connection is usable and perform database cursor wrapping.
        """
        self.validate_thread_sharing()
        if self.queries_logged:
            wrapped_cursor = self.make_debug_cursor(cursor)
        else:
            wrapped_cursor = self.make_cursor(cursor)
        return wrapped_cursor