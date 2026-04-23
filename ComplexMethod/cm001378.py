def _sanitize_path(
        self,
        path: str | Path,
    ) -> Path:
        """Resolve the relative path within the given root if possible.

        Parameters:
            relative_path: The relative path to resolve.

        Returns:
            Path: The resolved path.

        Raises:
            ValueError: If the path is absolute and a root is provided.
            ValueError: If the path is outside the root and the root is restricted.
        """

        # Posix systems disallow null bytes in paths. Windows is agnostic about it.
        # Do an explicit check here for all sorts of null byte representations.
        if "\0" in str(path):
            raise ValueError("Embedded null byte")

        logger.debug(f"Resolving path '{path}' in storage '{self.root}'")

        relative_path = Path(path)

        # Allow absolute paths if they are contained in the storage.
        if (
            relative_path.is_absolute()
            and self.restrict_to_root
            and not relative_path.is_relative_to(self.root)
        ):
            raise ValueError(
                f"Attempted to access absolute path '{relative_path}' "
                f"in storage '{self.root}'"
            )

        full_path = self.root / relative_path
        if self.is_local:
            full_path = full_path.resolve()
        else:
            full_path = Path(os.path.normpath(full_path))

        logger.debug(f"Joined paths as '{full_path}'")

        if self.restrict_to_root and not full_path.is_relative_to(self.root):
            raise ValueError(
                f"Attempted to access path '{full_path}' "
                f"outside of storage '{self.root}'."
            )

        return full_path