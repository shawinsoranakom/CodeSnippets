def create_archive(self, output_path: str, source_paths: list[str]) -> str:
        """Create an archive from specified files/directories.

        Args:
            output_path: Path for the output archive
            source_paths: List of files/directories to include

        Returns:
            str: Success message with archive details
        """
        archive_type = self._get_archive_type(output_path)

        if archive_type == "unknown":
            raise CommandExecutionError(
                "Unsupported archive format. Use .zip, .tar, .tar.gz, or .tar.bz2"
            )

        # Validate source paths exist
        for path in source_paths:
            if not self.workspace.exists(path):
                raise CommandExecutionError(f"Source path '{path}' does not exist")

        full_output = self.workspace.get_path(output_path)

        # Create parent directory if needed
        if directory := os.path.dirname(output_path):
            self.workspace.make_dir(directory)

        file_count = 0
        total_size = 0

        try:
            if archive_type == "zip":
                with zipfile.ZipFile(full_output, "w", zipfile.ZIP_DEFLATED) as zf:
                    for source in source_paths:
                        source_path = self.workspace.get_path(source)
                        if source_path.is_file():
                            zf.write(source_path, source)
                            file_count += 1
                            total_size += source_path.stat().st_size
                        elif source_path.is_dir():
                            for file in source_path.rglob("*"):
                                if file.is_file():
                                    arcname = str(
                                        Path(source) / file.relative_to(source_path)
                                    )
                                    zf.write(file, arcname)
                                    file_count += 1
                                    total_size += file.stat().st_size
            else:
                # Tar formats
                mode = "w"
                if archive_type == "tar.gz":
                    mode = "w:gz"
                elif archive_type == "tar.bz2":
                    mode = "w:bz2"

                with tarfile.open(full_output, mode) as tf:
                    for source in source_paths:
                        source_path = self.workspace.get_path(source)
                        tf.add(source_path, arcname=source)
                        if source_path.is_file():
                            file_count += 1
                            total_size += source_path.stat().st_size
                        else:
                            for file in source_path.rglob("*"):
                                if file.is_file():
                                    file_count += 1
                                    total_size += file.stat().st_size

            archive_size = full_output.stat().st_size
            compression_ratio = (
                round((1 - archive_size / total_size) * 100, 1) if total_size > 0 else 0
            )

            return json.dumps(
                {
                    "archive": output_path,
                    "type": archive_type,
                    "files_added": file_count,
                    "original_size_bytes": total_size,
                    "archive_size_bytes": archive_size,
                    "compression_ratio": f"{compression_ratio}%",
                },
                indent=2,
            )

        except Exception as e:
            raise CommandExecutionError(f"Failed to create archive: {e}")