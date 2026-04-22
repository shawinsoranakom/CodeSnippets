def _create_script_finished_message(
        self, status: "ForwardMsg.ScriptFinishedStatus.ValueType"
    ) -> ForwardMsg:
        """Create and return a script_finished ForwardMsg."""
        msg = ForwardMsg()
        msg.script_finished = status
        return msg