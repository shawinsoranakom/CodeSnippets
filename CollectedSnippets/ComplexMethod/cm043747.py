def list_files(self, dir_url: str) -> list[str]:
        """Return the list of filenames in a remote directory.

        Fetches the directory listing HTML page (caching per URL) and
        extracts every ``href="<filename>"`` that looks like an actual
        file (not a parent link, not an absolute URL).

        Parameters
        ----------
        dir_url : str
            URL of the directory (should end with ``/``).

        Returns
        -------
        list[str]
            Sorted list of filenames present in that directory.
        """
        import re  # pylint: disable=import-outside-toplevel

        if not dir_url.endswith("/"):
            dir_url += "/"

        if dir_url not in self._dir_cache:
            html = self._fetch_url_content(dir_url)
            # Pull every href value that is a plain filename (no slash prefix,
            # no absolute URL, no "../" parent link).
            raw = re.findall(r'href="([^"]+)"', html)
            files = sorted(
                f
                for f in raw
                if f
                and not f.startswith("/")
                and not f.startswith("http")
                and not f.startswith("?")
                and f != "../"
            )
            self._dir_cache[dir_url] = files

        return self._dir_cache[dir_url]