def __repr__(self) -> str:
        # If the runtime is NOT initialized, it is a method call outside
        # the streamlit app, so we avoid reading the secrets file as it may not exist.
        # If the runtime is initialized, display the contents of the file and
        # the file must already exist.
        """A string representation of the contents of the dict. Thread-safe."""
        if not runtime.exists():
            return f"{self.__class__.__name__}(file_path={self._file_path!r})"
        return repr(self._parse(True))