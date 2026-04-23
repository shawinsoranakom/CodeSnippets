def list_archive(self, archive_path: str) -> str:
        """List contents of an archive.

        Args:
            archive_path: Path to the archive

        Returns:
            str: JSON with archive contents
        """
        if not self.workspace.exists(archive_path):
            raise CommandExecutionError(f"Archive '{archive_path}' does not exist")

        archive_type = self._get_archive_type(archive_path)
        full_archive = self.workspace.get_path(archive_path)

        contents = []

        try:
            if archive_type == "zip":
                with zipfile.ZipFile(full_archive, "r") as zf:
                    for info in zf.infolist():
                        contents.append(
                            {
                                "name": info.filename,
                                "size": info.file_size,
                                "compressed_size": info.compress_size,
                                "is_dir": info.is_dir(),
                            }
                        )
            elif archive_type in ("tar", "tar.gz", "tar.bz2"):
                mode = "r"
                if archive_type == "tar.gz":
                    mode = "r:gz"
                elif archive_type == "tar.bz2":
                    mode = "r:bz2"

                with tarfile.open(full_archive, mode) as tf:
                    for member in tf.getmembers():
                        contents.append(
                            {
                                "name": member.name,
                                "size": member.size,
                                "is_dir": member.isdir(),
                            }
                        )
            else:
                raise CommandExecutionError(
                    f"Unsupported archive format: {archive_type}"
                )

            total_size = sum(item.get("size", 0) for item in contents)

            return json.dumps(
                {
                    "archive": archive_path,
                    "type": archive_type,
                    "file_count": len(contents),
                    "total_size_bytes": total_size,
                    "contents": contents,
                },
                indent=2,
            )

        except (zipfile.BadZipFile, tarfile.TarError) as e:
            raise CommandExecutionError(f"Invalid or corrupted archive: {e}")