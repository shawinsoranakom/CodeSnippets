def request_rerun(self, new_data: RerunData) -> bool:
        """Request that the ScriptRunner rerun its script.

        If the ScriptRunner has been stopped, this request can't be honored:
        return False.

        Otherwise, record the request and return True. The ScriptRunner will
        handle the rerun request as soon as it reaches an interrupt point.
        """

        with self._lock:
            if self._state == ScriptRequestType.STOP:
                # We can't rerun after being stopped.
                return False

            if self._state == ScriptRequestType.CONTINUE:
                # If we're running, we can handle a rerun request
                # unconditionally.
                self._state = ScriptRequestType.RERUN
                self._rerun_data = new_data
                return True

            if self._state == ScriptRequestType.RERUN:
                # If we have an existing Rerun request, we coalesce this
                # new request into it.
                if self._rerun_data.widget_states is None:
                    # The existing request's widget_states is None, which
                    # means it wants to rerun with whatever the most
                    # recent script execution's widget state was.
                    # We have no meaningful state to merge with, and
                    # so we simply overwrite the existing request.
                    self._rerun_data = new_data
                    return True

                if new_data.widget_states is not None:
                    # Both the existing and the new request have
                    # non-null widget_states. Merge them together.
                    coalesced_states = coalesce_widget_states(
                        self._rerun_data.widget_states, new_data.widget_states
                    )
                    self._rerun_data = RerunData(
                        query_string=new_data.query_string,
                        widget_states=coalesced_states,
                        page_script_hash=new_data.page_script_hash,
                        page_name=new_data.page_name,
                    )
                    return True

                # If old widget_states is NOT None, and new widget_states IS
                # None, then this new request is entirely redundant. Leave
                # our existing rerun_data as is.
                return True

            # We'll never get here
            raise RuntimeError(f"Unrecognized ScriptRunnerState: {self._state}")