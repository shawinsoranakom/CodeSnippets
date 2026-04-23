async def copy_to(self, src_path: str, dst_path: str) -> None:
        """Copies a file to the container.

        Args:
            src_path: Source file path (host).
            dst_path: Destination path (container).

        Raises:
            FileNotFoundError: If source file does not exist.
            RuntimeError: If copy operation fails.
        """
        try:
            if not os.path.exists(src_path):
                raise FileNotFoundError(f"Source file not found: {src_path}")

            # Create destination directory in container
            resolved_dst = self._safe_resolve_path(dst_path)
            container_dir = os.path.dirname(resolved_dst)
            if container_dir:
                await self.run_command(f"mkdir -p {container_dir}")

            # Create tar file to upload
            with tempfile.TemporaryDirectory() as tmp_dir:
                tar_path = os.path.join(tmp_dir, "temp.tar")
                with tarfile.open(tar_path, "w") as tar:
                    # Handle directory source path
                    if os.path.isdir(src_path):
                        os.path.basename(src_path.rstrip("/"))
                        for root, _, files in os.walk(src_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.join(
                                    os.path.basename(dst_path),
                                    os.path.relpath(file_path, src_path),
                                )
                                tar.add(file_path, arcname=arcname)
                    else:
                        # Add single file to tar
                        tar.add(src_path, arcname=os.path.basename(dst_path))

                # Read tar file content
                with open(tar_path, "rb") as f:
                    data = f.read()

                # Upload to container
                await asyncio.to_thread(
                    self.container.put_archive,
                    os.path.dirname(resolved_dst) or "/",
                    data,
                )

                # Verify file was created successfully
                try:
                    await self.run_command(f"test -e {resolved_dst}")
                except Exception:
                    raise RuntimeError(f"Failed to verify file creation: {dst_path}")

        except FileNotFoundError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to copy file: {e}")