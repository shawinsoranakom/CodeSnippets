def __init__(self, data):
        """
        Populate the initial data using __setitem__ to ensure values are
        correctly encoded.
        """
        self._store = {}
        if data:
            for header, value in self._unpack_items(data):
                self[header] = value