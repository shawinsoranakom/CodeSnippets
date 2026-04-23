def abspath(self) -> Optional[str]:
        """The absolute path that the component is served from."""
        if self.path is None:
            return None
        return os.path.abspath(self.path)