def _validate_and_resolve_path(self, path: str) -> Path:
        """Validate and resolve a virtual path to filesystem path.

        Args:
            path: Virtual path (e.g., `/file.txt` or `/src/main.py`).

        Returns:
            Resolved absolute filesystem path within `root_path`.

        Raises:
            ValueError: If path contains traversal attempts, escapes root directory,
                or violates `allowed_prefixes` restrictions.
        """
        # Normalize path
        if not path.startswith("/"):
            path = "/" + path

        # Check for path traversal
        if ".." in path or "~" in path:
            msg = "Path traversal not allowed"
            raise ValueError(msg)

        # Convert virtual path to filesystem path
        # Remove leading / and resolve relative to root
        relative = path.lstrip("/")
        full_path = (self.root_path / relative).resolve()

        # Ensure path is within root
        try:
            full_path.relative_to(self.root_path)
        except ValueError:
            msg = f"Path outside root directory: {path}"
            raise ValueError(msg) from None

        # Check allowed prefixes
        virtual_path = "/" + str(full_path.relative_to(self.root_path))
        if self.allowed_prefixes:
            allowed = any(
                virtual_path.startswith(prefix) or virtual_path == prefix.rstrip("/")
                for prefix in self.allowed_prefixes
            )
            if not allowed:
                msg = f"Path must start with one of: {self.allowed_prefixes}"
                raise ValueError(msg)

        return full_path