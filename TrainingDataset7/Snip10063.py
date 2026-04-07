def __exit__(self, type, value, traceback):
        # Close instead of passing through to avoid backend-specific behavior
        # (#17671). Catch errors liberally because errors in cleanup code
        # aren't useful.
        try:
            self.close()
        except self.db.Database.Error:
            pass