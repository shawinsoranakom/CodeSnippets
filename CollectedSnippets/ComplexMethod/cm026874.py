def extra_state_attributes(self) -> dict[str, Any]:
        """Get the state attributes for the device."""
        attr = {}
        if self._actions:
            attr["actions_enabled"] = self._actions.enabled
            if self._actions.last_finished != EMPTY_TIME:
                attr["actions_last_finished"] = self._actions.last_finished
            if self._actions.last_run != EMPTY_TIME:
                attr["actions_last_run"] = self._actions.last_run
            if self._actions.last_update != EMPTY_TIME:
                attr["actions_last_update"] = self._actions.last_update
            attr["ran_else"] = self._actions.ran_else
            attr["ran_then"] = self._actions.ran_then
            attr["run_at_startup"] = self._actions.run_at_startup
            attr["running"] = self._actions.running
        attr["status_enabled"] = self._node.enabled
        if self._node.last_finished != EMPTY_TIME:
            attr["status_last_finished"] = self._node.last_finished
        if self._node.last_run != EMPTY_TIME:
            attr["status_last_run"] = self._node.last_run
        if self._node.last_update != EMPTY_TIME:
            attr["status_last_update"] = self._node.last_update
        return attr