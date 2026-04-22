def _get_script_run_ctx(self) -> ScriptRunContext:
        """Get the ScriptRunContext for the current thread.

        Returns
        -------
        ScriptRunContext
            The ScriptRunContext for the current thread.

        Raises
        ------
        AssertionError
            If called outside of a ScriptRunner thread.
        RuntimeError
            If there is no ScriptRunContext for the current thread.

        """
        assert self._is_in_script_thread()

        ctx = get_script_run_ctx()
        if ctx is None:
            # This should never be possible on the script_runner thread.
            raise RuntimeError(
                "ScriptRunner thread has a null ScriptRunContext. Something has gone very wrong!"
            )
        return ctx