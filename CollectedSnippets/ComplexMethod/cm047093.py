def get_static_file(self, url, host=''):
        """
        Get the full-path of the file if the url resolves to a local
        static file, otherwise return None.

        Without the second host parameters, ``url`` must be an absolute
        path, others URLs are considered faulty.

        With the second host parameters, ``url`` can also be a full URI
        and the authority found in the URL (if any) is validated against
        the given ``host``.
        """

        netloc, path = urlparse(url)[1:3]
        try:
            path_netloc, module, static, resource = path.split('/', 3)
        except ValueError:
            return None

        if ((netloc and netloc != host) or (path_netloc and path_netloc != host)):
            return None

        if not (static == 'static' and resource):
            return None

        static_path = self.static_path(module)
        if not static_path:
            return None

        try:
            return file_path(opj(static_path, resource))
        except FileNotFoundError:
            return None