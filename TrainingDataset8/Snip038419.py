def get_absolute_path(cls, root: str, path: str) -> str:
        # All files are stored in memory, so the absolute path is just the
        # path itself. In the MediaFileHandler, it's just the filename
        return path