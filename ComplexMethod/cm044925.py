def install_from_zip(
        self,
        zip_path: Path,
        speckit_version: str,
        priority: int = 10,
    ) -> PresetManifest:
        """Install preset from ZIP file.

        Args:
            zip_path: Path to preset ZIP file
            speckit_version: Current spec-kit version
            priority: Resolution priority (lower = higher precedence, default 10)

        Returns:
            Installed preset manifest

        Raises:
            PresetValidationError: If manifest is invalid or priority is invalid
            PresetCompatibilityError: If pack is incompatible
        """
        # Validate priority early
        if priority < 1:
            raise PresetValidationError("Priority must be a positive integer (1 or higher)")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                temp_path_resolved = temp_path.resolve()
                for member in zf.namelist():
                    member_path = (temp_path / member).resolve()
                    try:
                        member_path.relative_to(temp_path_resolved)
                    except ValueError:
                        raise PresetValidationError(
                            f"Unsafe path in ZIP archive: {member} "
                            "(potential path traversal)"
                        )
                zf.extractall(temp_path)

            pack_dir = temp_path
            manifest_path = pack_dir / "preset.yml"

            if not manifest_path.exists():
                subdirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if len(subdirs) == 1:
                    pack_dir = subdirs[0]
                    manifest_path = pack_dir / "preset.yml"

            if not manifest_path.exists():
                raise PresetValidationError(
                    "No preset.yml found in ZIP file"
                )

            return self.install_from_directory(pack_dir, speckit_version, priority)