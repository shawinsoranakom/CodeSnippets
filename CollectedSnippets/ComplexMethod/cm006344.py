async def save_file(self, flow_id: str, file_name: str, data: bytes, *, append: bool = False) -> None:
        """Save a file in the local storage.

        Args:
            flow_id: The identifier for the flow.
            file_name: The name of the file to be saved.
            data: The byte content of the file.
            append: If True, append to existing file; if False, overwrite.

        Raises:
            FileNotFoundError: If the specified flow does not exist.
            IsADirectoryError: If the file name is a directory.
            PermissionError: If there is no permission to write the file.
            ValueError: If path traversal is detected (security violation).
        """
        # SECURITY FIX: Defense-in-depth path containment check to prevent directory traversal
        # Validate BEFORE creating any directories to prevent race conditions
        # This ensures the resolved absolute path stays within the intended flow directory
        # even if the API layer validation is bypassed or has bugs.
        folder_path = self.data_dir / flow_id
        file_path = folder_path / file_name

        try:
            # Resolve paths to their absolute canonical forms
            # Note: resolve() works even if the path doesn't exist yet
            resolved_folder_path = await folder_path.resolve()
            resolved_file_path = await file_path.resolve()

            # Check if the resolved file path is actually within the flow directory
            # Using is_relative_to() ensures no path traversal can escape the boundary
            # Example attack: file_name="../../etc/passwd" would resolve outside folder_path
            if not resolved_file_path.is_relative_to(resolved_folder_path):
                # SECURITY: Don't log the actual paths to avoid information disclosure
                await logger.aerror(
                    f"Path traversal attempt detected for flow_id='{flow_id}'. "
                    "File path would escape flow directory boundary."
                )
                msg = "Invalid file path: path traversal detected"
                raise ValueError(msg)

            # Additional check: ensure file_name doesn't contain path separators
            # This catches cases where Path() might normalize away dangerous sequences
            if "/" in file_name or "\\" in file_name or ".." in file_name:
                await logger.aerror(
                    f"Invalid file_name contains path separators or traversal sequences: flow_id='{flow_id}'"
                )
                msg = "Invalid file name: contains path separators"
                raise ValueError(msg)

        except ValueError:
            # Re-raise ValueError (our security checks)
            raise
        except AttributeError:
            # is_relative_to() not available (Python < 3.9), fall back to string comparison
            # This should never happen in production but provides compatibility
            resolved_folder_str = str(await folder_path.resolve())
            resolved_file_str = str(await file_path.resolve())
            if not resolved_file_str.startswith(resolved_folder_str):
                await logger.aerror(f"Path traversal attempt detected for flow_id='{flow_id}' (fallback check)")
                msg = "Invalid file path: path traversal detected"
                raise ValueError(msg) from None
        except Exception as e:
            # Log unexpected errors during path resolution but don't expose details to user
            await logger.aerror(f"Error validating file path for flow_id='{flow_id}': {type(e).__name__}")
            msg = "Invalid file path"
            raise ValueError(msg) from e

        # Only create directory after validation passes
        await folder_path.mkdir(parents=True, exist_ok=True)

        try:
            mode = "ab" if append else "wb"
            async with aiofiles.open(str(file_path), mode) as f:
                await f.write(data)
            action = "appended to" if append else "saved"
            await logger.ainfo(f"File {file_name} {action} successfully in flow {flow_id}.")
        except Exception:
            logger.exception(f"Error saving file {file_name} in flow {flow_id}")
            raise