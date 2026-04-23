def __init__(self, connection_reset=False):
        """
        If ``connection_reset`` is ``True``, Django knows will halt the upload
        without consuming the rest of the upload. This will cause the browser
        to show a "connection reset" error.
        """
        self.connection_reset = connection_reset