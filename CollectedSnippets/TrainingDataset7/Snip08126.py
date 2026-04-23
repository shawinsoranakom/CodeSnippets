def file_path(self, url):
        """
        Return the relative path to the media file on disk for the given URL.
        """
        relative_url = url.removeprefix(self.base_url.path)
        return url2pathname(relative_url)