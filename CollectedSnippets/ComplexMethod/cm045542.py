async def copy_from(self, src_path: str, dst_path: str) -> None:
        """Copies a file from the container.

        Args:
            src_path: Source file path (container).
            dst_path: Destination path (host).

        Raises:
            FileNotFoundError: If source file does not exist.
            RuntimeError: If copy operation fails.
        """
        try:
            # Ensure destination file's parent directory exists
            parent_dir = os.path.dirname(dst_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            # Get file stream
            resolved_src = self._safe_resolve_path(src_path)
            stream, stat = await asyncio.to_thread(
                self.container.get_archive, resolved_src
            )

            # Create temporary directory to extract file
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Write stream to temporary file
                tar_path = os.path.join(tmp_dir, "temp.tar")
                with open(tar_path, "wb") as f:
                    for chunk in stream:
                        f.write(chunk)

                # Extract file
                with tarfile.open(tar_path) as tar:
                    members = tar.getmembers()
                    if not members:
                        raise FileNotFoundError(f"Source file is empty: {src_path}")

                    # If destination is a directory, we should preserve relative path structure
                    if os.path.isdir(dst_path):
                        tar.extractall(dst_path)
                    else:
                        # If destination is a file, we only extract the source file's content
                        if len(members) > 1:
                            raise RuntimeError(
                                f"Source path is a directory but destination is a file: {src_path}"
                            )

                        with open(dst_path, "wb") as dst:
                            src_file = tar.extractfile(members[0])
                            if src_file is None:
                                raise RuntimeError(
                                    f"Failed to extract file: {src_path}"
                                )
                            dst.write(src_file.read())

        except docker.errors.NotFound:
            raise FileNotFoundError(f"Source file not found: {src_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to copy file: {e}")