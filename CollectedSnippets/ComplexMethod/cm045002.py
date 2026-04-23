def check_modified(self) -> list[str]:
        """Return relative paths of tracked files whose content changed on disk."""
        modified: list[str] = []
        for rel, expected_hash in self._files.items():
            rel_path = Path(rel)
            # Skip paths that are absolute or attempt to escape the project root
            if rel_path.is_absolute() or ".." in rel_path.parts:
                continue
            abs_path = self.project_root / rel_path
            if not abs_path.exists() and not abs_path.is_symlink():
                continue
            # Treat symlinks and non-regular-files as modified
            if abs_path.is_symlink() or not abs_path.is_file():
                modified.append(rel)
                continue
            if _sha256(abs_path) != expected_hash:
                modified.append(rel)
        return modified