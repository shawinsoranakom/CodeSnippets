async def async_configure(
        self, flow_id: str, user_input: dict | None = None
    ) -> _FlowResultT:
        """Continue a data entry flow."""
        result: _FlowResultT | None = None

        # Workaround for flow handlers which have not been upgraded to pass a show
        # progress task, needed because of the change to eager tasks in HA Core 2024.5,
        # can be removed in HA Core 2024.8.
        flow = self._progress.get(flow_id)
        if flow and flow.deprecated_show_progress:
            if (cur_step := flow.cur_step) and cur_step[
                "type"
            ] == FlowResultType.SHOW_PROGRESS:
                # Allow the progress task to finish before we call the flow handler
                await asyncio.sleep(0)

        while not result or result["type"] == FlowResultType.SHOW_PROGRESS_DONE:
            result = await self._async_configure(flow_id, user_input)
            flow = self._progress.get(flow_id)
            if flow and flow.deprecated_show_progress:
                break
        return result