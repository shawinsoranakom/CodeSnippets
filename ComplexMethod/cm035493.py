def _confirm_cwd(self) -> None:
        """Confirms the actual CWD in the runspace and updates self._cwd."""
        ps_confirm = None
        try:
            ps_confirm = PowerShell.Create()
            ps_confirm.Runspace = self.runspace
            ps_confirm.AddScript('Get-Location')
            results = ps_confirm.Invoke()
            if results and results.Count > 0 and hasattr(results[0], 'Path'):
                actual_cwd = str(results[0].Path)
                if os.path.isdir(actual_cwd):
                    if actual_cwd != self._cwd:
                        logger.warning(
                            f'Runspace CWD ({actual_cwd}) differs from expected ({self._cwd}). Updating session CWD.'
                        )
                        self._cwd = actual_cwd
                    else:
                        logger.debug(f'Confirmed runspace CWD is {self._cwd}')
                else:
                    logger.error(
                        f'Get-Location returned an invalid path: {actual_cwd}. Session CWD may be inaccurate.'
                    )
            elif ps_confirm.Streams.Error:
                errors = '\n'.join([str(err) for err in ps_confirm.Streams.Error])
                logger.error(f'Error confirming runspace CWD: {errors}')
            else:
                logger.error('Could not confirm runspace CWD (No result or error).')
        except Exception as e:
            logger.error(f'Exception confirming CWD: {e}')
        finally:
            if ps_confirm:
                ps_confirm.Dispose()