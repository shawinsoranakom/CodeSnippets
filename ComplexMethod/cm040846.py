def from_state_props(self, state_props: StateProps) -> None:
        super().from_state_props(state_props=state_props)
        self.result_path = state_props.get(ResultPath) or ResultPath(
            result_path_src=ResultPath.DEFAULT_PATH
        )
        self.result_selector = state_props.get(ResultSelector)
        self.retry = state_props.get(RetryDecl)
        self.catch = state_props.get(CatchDecl)

        # If provided, the "HeartbeatSeconds" interval MUST be smaller than the "TimeoutSeconds" value.
        # If not provided, the default value of "TimeoutSeconds" is 60.
        timeout = state_props.get(Timeout)
        heartbeat = state_props.get(Heartbeat)
        if isinstance(timeout, TimeoutSeconds) and isinstance(heartbeat, HeartbeatSeconds):
            if timeout.timeout_seconds <= heartbeat.heartbeat_seconds:
                raise RuntimeError(
                    f"'HeartbeatSeconds' interval MUST be smaller than the 'TimeoutSeconds' value, "
                    f"got '{timeout.timeout_seconds}' and '{heartbeat.heartbeat_seconds}' respectively."
                )
        if heartbeat is not None and timeout is None:
            timeout = TimeoutSeconds(timeout_seconds=60, is_default=True)

        if timeout is not None:
            self.timeout = timeout
        if heartbeat is not None:
            self.heartbeat = heartbeat