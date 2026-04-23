def guess_type(self, url, strict=True):
        """Guess the type of a file which is either a URL or a path-like object.

        Return value is a tuple (type, encoding) where type is None if
        the type can't be guessed (no or unknown suffix) or a string
        of the form type/subtype, usable for a MIME Content-type
        header; and encoding is None for no encoding or the name of
        the program used to encode (e.g. compress or gzip).  The
        mappings are table driven.  Encoding suffixes are case
        sensitive; type suffixes are first tried case sensitive, then
        case insensitive.

        The suffixes .tgz, .taz and .tz (case sensitive!) are all
        mapped to '.tar.gz'.  (This is table-driven too, using the
        dictionary suffix_map.)

        Optional 'strict' argument when False adds a bunch of commonly found,
        but non-standard types.
        """
        # Lazy import to improve module import time
        import os
        import urllib.parse

        # TODO: Deprecate accepting file paths (in particular path-like objects).
        url = os.fspath(url)
        p = urllib.parse.urlparse(url)
        if p.scheme and len(p.scheme) > 1:
            scheme = p.scheme
            url = p.path
        else:
            return self.guess_file_type(url, strict=strict)
        if scheme == 'data':
            # syntax of data URLs:
            # dataurl   := "data:" [ mediatype ] [ ";base64" ] "," data
            # mediatype := [ type "/" subtype ] *( ";" parameter )
            # data      := *urlchar
            # parameter := attribute "=" value
            # type/subtype defaults to "text/plain"
            comma = url.find(',')
            if comma < 0:
                # bad data URL
                return None, None
            semi = url.find(';', 0, comma)
            if semi >= 0:
                type = url[:semi]
            else:
                type = url[:comma]
            if '=' in type or '/' not in type:
                type = 'text/plain'
            return type, None           # never compressed, so encoding is None

        # Lazy import to improve module import time
        import posixpath

        return self._guess_file_type(url, strict, posixpath.splitext)