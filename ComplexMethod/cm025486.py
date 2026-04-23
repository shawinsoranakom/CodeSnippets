async def async_cancel_command(
        self, commands_to_cancel: list[OverkizCommand]
    ) -> bool:
        """Cancel running execution by command."""

        # Cancel a running execution
        # Retrieve executions initiated via Home Assistant from Data Update Coordinator queue
        exec_id = next(
            (
                exec_id
                # Reverse dictionary to cancel the last added execution
                for exec_id, execution in reversed(self.coordinator.executions.items())
                if execution.get("device_url") == self.device.device_url
                and execution.get("command_name") in commands_to_cancel
            ),
            None,
        )

        if exec_id:
            await self.async_cancel_execution(exec_id)
            return True

        # Retrieve executions initiated outside Home Assistant via API
        executions = cast(Any, await self.coordinator.client.get_current_executions())
        # executions.action_group is typed incorrectly in the upstream library
        # or the below code is incorrect.
        exec_id = next(
            (
                execution.id
                for execution in executions
                # Reverse dictionary to cancel the last added execution
                for action in reversed(execution.action_group.get("actions"))
                for command in action.get("commands")
                if action.get("device_url") == self.device.device_url
                and command.get("name") in commands_to_cancel
            ),
            None,
        )

        if exec_id:
            await self.async_cancel_execution(exec_id)
            return True

        return False