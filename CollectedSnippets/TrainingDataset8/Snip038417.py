def get_content_size(self) -> int:
        abspath = self.absolute_path
        if abspath is None:
            return 0

        media_file = self._storage.get_file(abspath)
        return media_file.content_size