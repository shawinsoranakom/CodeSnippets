def __init__(self, server, params, library, value_not_found_exception):
        super().__init__(params)
        if isinstance(server, str):
            self._servers = re.split("[;,]", server)
        else:
            self._servers = server

        # Exception type raised by the underlying client library for a
        # nonexistent key.
        self.LibraryValueNotFoundException = value_not_found_exception

        self._lib = library
        self._class = library.Client
        self._options = params.get("OPTIONS") or {}