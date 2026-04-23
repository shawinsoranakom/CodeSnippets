def _get_current_cwd(self) -> str:
        """Gets the current working directory from the runspace."""
        # Use helper to run Get-Location
        results = self._run_ps_command('Get-Location')

        # --- Add more detailed check logging ---
        if results and results.Count > 0:  # type: ignore[attr-defined]
            first_result = results[0]
            has_path_attr = hasattr(first_result, 'Path')

            if has_path_attr:
                # Original logic resumes here if hasattr is True
                fetched_cwd = str(first_result.Path)
                if os.path.isdir(fetched_cwd):
                    if fetched_cwd != self._cwd:
                        logger.info(
                            f"_get_current_cwd: Fetched CWD '{fetched_cwd}' differs from cached '{self._cwd}'. Updating cache."
                        )
                        self._cwd = fetched_cwd
                    return self._cwd
                else:
                    logger.warning(
                        f"_get_current_cwd: Path '{fetched_cwd}' is not a valid directory. Returning cached CWD: {self._cwd}"
                    )
                    return self._cwd
            else:
                # Handle cases where Path attribute is missing (e.g., unexpected object type)
                # Maybe the path is in BaseObject?
                try:
                    base_object = first_result.BaseObject
                    if hasattr(base_object, 'Path'):
                        fetched_cwd = str(base_object.Path)
                        if os.path.isdir(fetched_cwd):
                            if fetched_cwd != self._cwd:
                                logger.info(
                                    f"_get_current_cwd: Fetched CWD '{fetched_cwd}' (from BaseObject) differs from cached '{self._cwd}'. Updating cache."
                                )
                                self._cwd = fetched_cwd
                            return self._cwd
                        else:
                            logger.warning(
                                f"_get_current_cwd: Path '{fetched_cwd}' (from BaseObject) is not a valid directory. Returning cached CWD: {self._cwd}"
                            )
                            return self._cwd
                    else:
                        logger.error(
                            f'_get_current_cwd: BaseObject also lacks Path attribute. Cannot determine CWD from result: {first_result}'
                        )
                        return self._cwd  # Return cached
                except AttributeError as ae:
                    logger.error(
                        f'_get_current_cwd: Error accessing BaseObject or its Path: {ae}. Result: {first_result}'
                    )
                    return self._cwd  # Return cached
                except Exception as ex:
                    logger.error(
                        f'_get_current_cwd: Unexpected error checking BaseObject: {ex}. Result: {first_result}'
                    )
                    return self._cwd  # Return cached

        # This path is taken if _run_ps_command returned [] or results.Count was 0
        logger.error(
            f'_get_current_cwd: No valid results received from Get-Location call. Returning cached CWD: {self._cwd}'
        )
        return self._cwd