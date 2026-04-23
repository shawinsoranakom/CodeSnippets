def uninstall(
        self,
        project_root: Path | None = None,
        *,
        force: bool = False,
    ) -> tuple[list[Path], list[Path]]:
        """Remove tracked files whose hash still matches.

        Parameters:
            project_root: Override for the project root.
            force:        If ``True``, remove files even if modified.

        Returns:
            ``(removed, skipped)`` — absolute paths.
        """
        root = (project_root or self.project_root).resolve()
        removed: list[Path] = []
        skipped: list[Path] = []

        for rel, expected_hash in self._files.items():
            # Use non-resolved path for deletion so symlinks themselves
            # are removed, not their targets.
            path = root / rel
            # Validate containment lexically (without following symlinks)
            # by collapsing .. segments via Path resolution on the string parts.
            try:
                normed = Path(os.path.normpath(path))
                normed.relative_to(root)
            except (ValueError, OSError):
                continue
            if not path.exists() and not path.is_symlink():
                continue
            # Skip directories — manifest only tracks files
            if not path.is_file() and not path.is_symlink():
                skipped.append(path)
                continue
            # Never follow symlinks when comparing hashes. Only remove
            # symlinks when forced, to avoid acting on tampered entries.
            if path.is_symlink():
                if not force:
                    skipped.append(path)
                    continue
            else:
                if not force and _sha256(path) != expected_hash:
                    skipped.append(path)
                    continue
            try:
                path.unlink()
            except OSError:
                skipped.append(path)
                continue
            removed.append(path)
            # Clean up empty parent directories up to project root
            parent = path.parent
            while parent != root:
                try:
                    parent.rmdir()  # only succeeds if empty
                except OSError:
                    break
                parent = parent.parent

        # Remove the manifest file itself
        manifest = root / ".specify" / "integrations" / f"{self.key}.manifest.json"
        if manifest.exists():
            manifest.unlink()
            parent = manifest.parent
            while parent != root:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent

        return removed, skipped