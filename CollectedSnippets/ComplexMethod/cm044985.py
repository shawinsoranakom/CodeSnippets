def install_from_zip(
        self,
        zip_path: Path,
        speckit_version: str,
        priority: int = 10,
    ) -> ExtensionManifest:
        """Install extension from ZIP file.

        Args:
            zip_path: Path to extension ZIP file
            speckit_version: Current spec-kit version
            priority: Resolution priority (lower = higher precedence, default 10)

        Returns:
            Installed extension manifest

        Raises:
            ValidationError: If manifest is invalid or priority is invalid
            CompatibilityError: If extension is incompatible
        """
        # Validate priority early
        if priority < 1:
            raise ValidationError("Priority must be a positive integer (1 or higher)")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            # Extract ZIP safely (prevent Zip Slip attack)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Validate all paths first before extracting anything
                temp_path_resolved = temp_path.resolve()
                for member in zf.namelist():
                    member_path = (temp_path / member).resolve()
                    # Use is_relative_to for safe path containment check
                    try:
                        member_path.relative_to(temp_path_resolved)
                    except ValueError:
                        raise ValidationError(
                            f"Unsafe path in ZIP archive: {member} (potential path traversal)"
                        )
                # Only extract after all paths are validated
                zf.extractall(temp_path)

            # Find extension directory (may be nested)
            extension_dir = temp_path
            manifest_path = extension_dir / "extension.yml"

            # Check if manifest is in a subdirectory
            if not manifest_path.exists():
                subdirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    extension_dir = subdirs[0]
                    manifest_path = extension_dir / "extension.yml"

            if not manifest_path.exists():
                raise ValidationError("No extension.yml found in ZIP file")

            # Install from extracted directory
            return self.install_from_directory(extension_dir, speckit_version, priority=priority)