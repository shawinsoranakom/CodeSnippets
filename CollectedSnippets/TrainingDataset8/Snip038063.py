def request_rerun(self, rerun_data: RerunData) -> bool:
        """Request that the ScriptRunner interrupt its currently-running
        script and restart it.

        If the ScriptRunner has been stopped, this request can't be honored:
        return False.

        Otherwise, record the request and return True. The ScriptRunner will
        handle the rerun request as soon as it reaches an interrupt point.

        Safe to call from any thread.
        """
        return self._requests.request_rerun(rerun_data)