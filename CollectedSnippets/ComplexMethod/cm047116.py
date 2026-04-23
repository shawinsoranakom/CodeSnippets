def get_file_location(
        self, pathformat: str | None = None
    ) -> tuple[str | None, str | None]:
        """Returns a tuple with the location of the file in the form
        ``(server, location)``.  If the netloc is empty in the URL or
        points to localhost, it's represented as ``None``.

        The `pathformat` by default is autodetection but needs to be set
        when working with URLs of a specific system.  The supported values
        are ``'windows'`` when working with Windows or DOS paths and
        ``'posix'`` when working with posix paths.

        If the URL does not point to a local file, the server and location
        are both represented as ``None``.

        :param pathformat: The expected format of the path component.
                           Currently ``'windows'`` and ``'posix'`` are
                           supported.  Defaults to ``None`` which is
                           autodetect.
        """
        if self.scheme != "file":
            return None, None

        path = url_unquote(self.path)
        host = self.netloc or None

        if pathformat is None:
            if os.name == "nt":
                pathformat = "windows"
            else:
                pathformat = "posix"

        if pathformat == "windows":
            if path[:1] == "/" and path[1:2].isalpha() and path[2:3] in "|:":
                path = f"{path[1:2]}:{path[3:]}"
            windows_share = path[:3] in ("\\" * 3, "/" * 3)
            import ntpath

            path = ntpath.normpath(path)
            # Windows shared drives are represented as ``\\host\\directory``.
            # That results in a URL like ``file://///host/directory``, and a
            # path like ``///host/directory``. We need to special-case this
            # because the path contains the hostname.
            if windows_share and host is None:
                parts = path.lstrip("\\").split("\\", 1)
                if len(parts) == 2:
                    host, path = parts
                else:
                    host = parts[0]
                    path = ""
        elif pathformat == "posix":
            import posixpath

            path = posixpath.normpath(path)
        else:
            raise TypeError(f"Invalid path format {pathformat!r}")

        if host in ("127.0.0.1", "::1", "localhost"):
            host = None

        return host, path