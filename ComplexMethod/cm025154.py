async def _async_handle_step(
        self,
        flow: FlowHandler[_FlowContextT, _FlowResultT, _HandlerT],
        step_id: str,
        user_input: dict | BaseServiceInfo | None,
    ) -> _FlowResultT:
        """Handle a step of a flow."""
        self._raise_if_step_does_not_exist(flow, step_id)

        method = f"async_step_{step_id}"
        try:
            result: _FlowResultT = await getattr(flow, method)(user_input)
        except AbortFlow as err:
            result = self._flow_result(
                type=FlowResultType.ABORT,
                flow_id=flow.flow_id,
                handler=flow.handler,
                reason=err.reason,
                description_placeholders=err.description_placeholders,
            )

        if flow.flow_id not in self._progress:
            # The flow was removed during the step, raise UnknownFlow
            # unless the result is an abort
            if result["type"] != FlowResultType.ABORT:
                raise UnknownFlow
            return result

        # Setup the flow handler's preview if needed
        if result.get("preview") is not None:
            await self._async_setup_preview(flow)

        if not isinstance(result["type"], FlowResultType):
            result["type"] = FlowResultType(result["type"])  # type: ignore[unreachable]
            report_usage(
                "does not use FlowResultType enum for data entry flow result type",
                core_behavior=ReportBehavior.LOG,
                breaks_in_ha_version="2025.1",
            )

        if (
            result["type"] == FlowResultType.SHOW_PROGRESS
            # Mypy does not agree with using pop on _FlowResultT
            and (progress_task := result.pop("progress_task", None))  # type: ignore[arg-type]
            and progress_task != flow.async_get_progress_task()
        ):
            # The flow's progress task was changed, register a callback on it
            async def call_configure() -> None:
                with suppress(UnknownFlow):
                    await self._async_configure(flow.flow_id)

            def schedule_configure(_: asyncio.Task) -> None:
                self.hass.async_create_task(call_configure())

            # The mypy ignores are a consequence of mypy not accepting the pop above
            progress_task.add_done_callback(schedule_configure)  # type: ignore[attr-defined]
            flow.async_set_progress_task(progress_task)  # type: ignore[arg-type]

        elif result["type"] != FlowResultType.SHOW_PROGRESS:
            flow.async_cancel_progress_task()

        if result["type"] in STEP_ID_OPTIONAL_STEPS:
            if "step_id" not in result:
                result["step_id"] = step_id

        if result["type"] in FLOW_NOT_COMPLETE_STEPS:
            self._raise_if_step_does_not_exist(flow, result["step_id"])
            flow.cur_step = result
            return result

        try:
            # We pass a copy of the result because we're mutating our version
            result = await self.async_finish_flow(flow, result.copy())
        except AbortFlow as err:
            result = self._flow_result(
                type=FlowResultType.ABORT,
                flow_id=flow.flow_id,
                handler=flow.handler,
                reason=err.reason,
                description_placeholders=err.description_placeholders,
            )

        # _async_finish_flow may change result type, check it again
        if result["type"] == FlowResultType.FORM:
            flow.cur_step = result
            return result

        # Abort and Success results both finish the flow.
        self._async_remove_flow_progress(flow.flow_id)

        return result