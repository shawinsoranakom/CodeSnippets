async def _read_process_output_and_extract_error(
        self,
        process: subprocess.Popen,
        oauth_server_url: str | None,
        timeout: float = 2.0,
        stdout_file=None,
        stderr_file=None,
    ) -> tuple[str, str, str]:
        """Read process output and extract user-friendly error message.

        Args:
            process: The subprocess to read from
            oauth_server_url: OAuth server URL for error messages
            timeout: Timeout for reading output
            stdout_file: Optional file handle for stdout (Windows)
            stderr_file: Optional file handle for stderr (Windows)

        Returns:
            Tuple of (stdout, stderr, error_message)
        """
        stdout_content = ""
        stderr_content = ""

        try:
            # On Windows with temp files, read from files instead of pipes
            if stdout_file and stderr_file:
                # Close file handles to flush and allow reading
                try:
                    stdout_file.close()
                    stderr_file.close()
                except Exception as e:  # noqa: BLE001
                    await logger.adebug(f"Error closing temp files: {e}")

                # Read from temp files using asyncio.to_thread
                try:

                    def read_file(filepath):
                        return Path(filepath).read_bytes()

                    stdout_bytes = await asyncio.to_thread(read_file, stdout_file.name)
                    stdout_content = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
                except Exception as e:  # noqa: BLE001
                    await logger.adebug(f"Error reading stdout file: {e}")

                try:

                    def read_file(filepath):
                        return Path(filepath).read_bytes()

                    stderr_bytes = await asyncio.to_thread(read_file, stderr_file.name)
                    stderr_content = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
                except Exception as e:  # noqa: BLE001
                    await logger.adebug(f"Error reading stderr file: {e}")

                # Clean up temp files
                try:
                    Path(stdout_file.name).unlink()
                    Path(stderr_file.name).unlink()
                except Exception as e:  # noqa: BLE001
                    await logger.adebug(f"Error removing temp files: {e}")
            else:
                # Use asyncio.to_thread to avoid blocking the event loop
                # Process returns bytes, decode with error handling
                stdout_bytes, stderr_bytes = await asyncio.to_thread(process.communicate, timeout=timeout)
                stdout_content = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
                stderr_content = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

        except subprocess.TimeoutExpired:
            process.kill()
            error_msg = self._extract_error_message("", "", oauth_server_url)
            return "", "", error_msg

        error_msg = self._extract_error_message(stdout_content, stderr_content, oauth_server_url)
        return stdout_content, stderr_content, error_msg