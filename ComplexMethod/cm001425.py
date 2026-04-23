def extract_archive(
        self,
        archive_path: str,
        destination: str = ".",
        members: list[str] | None = None,
    ) -> str:
        """Extract files from an archive.

        Args:
            archive_path: Path to the archive
            destination: Directory to extract to
            members: Specific files to extract

        Returns:
            str: Success message with extraction details
        """
        if not self.workspace.exists(archive_path):
            raise CommandExecutionError(f"Archive '{archive_path}' does not exist")

        archive_type = self._get_archive_type(archive_path)
        full_archive = self.workspace.get_path(archive_path)
        full_dest = self.workspace.get_path(destination)

        # Check archive size
        archive_size = full_archive.stat().st_size
        max_size = self.config.max_archive_size
        if archive_size > max_size:
            raise CommandExecutionError(
                f"Archive too large: {archive_size} bytes (max: {max_size})"
            )

        # Create destination directory
        self.workspace.make_dir(destination)

        extracted_count = 0

        try:
            if archive_type == "zip":
                with zipfile.ZipFile(full_archive, "r") as zf:
                    # Security check for zip slip attack
                    for name in zf.namelist():
                        member_path = (full_dest / name).resolve()
                        if not str(member_path).startswith(str(full_dest.resolve())):
                            raise CommandExecutionError(
                                f"Unsafe archive: '{name}' extracts outside dest"
                            )

                    # Check total uncompressed size
                    total_size = sum(info.file_size for info in zf.infolist())
                    if total_size > self.config.max_extracted_size:
                        raise CommandExecutionError(
                            f"Archive content too large: {total_size} bytes "
                            f"(max: {self.config.max_extracted_size})"
                        )

                    if members:
                        for member in members:
                            zf.extract(member, full_dest)
                            extracted_count += 1
                    else:
                        zf.extractall(full_dest)
                        extracted_count = len(zf.namelist())

            elif archive_type in ("tar", "tar.gz", "tar.bz2"):
                mode = "r"
                if archive_type == "tar.gz":
                    mode = "r:gz"
                elif archive_type == "tar.bz2":
                    mode = "r:bz2"

                with tarfile.open(full_archive, mode) as tf:
                    # Security check for path traversal
                    for member in tf.getmembers():
                        member_path = (full_dest / member.name).resolve()
                        if not str(member_path).startswith(str(full_dest.resolve())):
                            raise CommandExecutionError(
                                f"Unsafe archive: '{member.name}' extracts outside dest"
                            )

                    if members:
                        for member in members:
                            tf.extract(member, full_dest)
                            extracted_count += 1
                    else:
                        tf.extractall(full_dest)
                        extracted_count = len(tf.getmembers())
            else:
                raise CommandExecutionError(
                    f"Unsupported archive format: {archive_type}"
                )

            return json.dumps(
                {
                    "archive": archive_path,
                    "destination": destination,
                    "files_extracted": extracted_count,
                },
                indent=2,
            )

        except (zipfile.BadZipFile, tarfile.TarError) as e:
            raise CommandExecutionError(f"Invalid or corrupted archive: {e}")
        except Exception as e:
            raise CommandExecutionError(f"Extraction failed: {e}")