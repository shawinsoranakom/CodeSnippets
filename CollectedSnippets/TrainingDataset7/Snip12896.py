def encoding(self, val):
        """
        Set the encoding used for GET/POST accesses. If the GET or POST
        dictionary has already been created, remove and recreate it on the
        next access (so that it is decoded correctly).
        """
        self._encoding = val
        if hasattr(self, "GET"):
            del self.GET
        if hasattr(self, "_post"):
            del self._post