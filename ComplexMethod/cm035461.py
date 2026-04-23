def copy_to(self, host_src: str, sandbox_dest: str, recursive: bool = False):
        """Copy a file or directory from the host to the sandbox."""
        if not self._runtime_initialized:
            raise RuntimeError('Runtime not initialized')
        if not os.path.exists(host_src):  # Source must exist on host
            raise FileNotFoundError(f"Source path '{host_src}' does not exist.")

        dest = self._sanitize_filename(sandbox_dest)

        try:
            # Case 1: Source is a directory and recursive copy.
            if os.path.isdir(host_src) and recursive:
                # Target is dest / basename(host_src)
                final_target_dir = os.path.join(dest, os.path.basename(host_src))

                # If source and final target are the same, skip.
                if os.path.realpath(host_src) == os.path.realpath(final_target_dir):
                    logger.debug(
                        'Skipping recursive copy: source and target are identical.'
                    )
                    pass
                else:
                    # Ensure parent of final_target_dir exists.
                    os.makedirs(dest, exist_ok=True)
                    shutil.copytree(host_src, final_target_dir, dirs_exist_ok=True)
                    # Why: Copies dir host_src into dest. Merges if target exists.

            # Case 2: Source is a file.
            elif os.path.isfile(host_src):
                final_target_file_path: str
                # Scenario A: sandbox_dest is clearly a directory.
                if os.path.isdir(dest) or (sandbox_dest.endswith(('/', os.sep))):
                    target_dir = dest
                    os.makedirs(target_dir, exist_ok=True)
                    final_target_file_path = os.path.join(
                        target_dir, os.path.basename(host_src)
                    )
                    # Why: Copies file into specified directory.

                # Scenario B: sandbox_dest is likely a new directory (e.g., 'new_dir').
                elif not os.path.exists(dest) and '.' not in os.path.basename(dest):
                    target_dir = dest
                    os.makedirs(target_dir, exist_ok=True)
                    final_target_file_path = os.path.join(
                        target_dir, os.path.basename(host_src)
                    )
                    # Why: Creates 'new_dir' and copies file into it.

                # Scenario C: sandbox_dest is a full file path.
                else:
                    final_target_file_path = dest
                    os.makedirs(os.path.dirname(final_target_file_path), exist_ok=True)
                    # Why: Copies file to a specific path, possibly renaming.

                shutil.copy2(host_src, final_target_file_path)

            else:  # Source is not a valid file or directory.
                raise FileNotFoundError(
                    f"Source path '{host_src}' is not a valid file or directory."
                )

        except FileNotFoundError as e:
            logger.error(f'File not found during copy: {str(e)}')
            raise
        except shutil.SameFileError as e:
            # We can be lenient here, just ignore this error.
            logger.debug(
                f'Skipping copy as source and destination are the same: {str(e)}'
            )
            pass
        except Exception as e:
            logger.error(f'Unexpected error copying file: {str(e)}')
            raise RuntimeError(f'Unexpected error copying file: {str(e)}')