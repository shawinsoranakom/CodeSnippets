async def _async_configure(
        self, flow_id: str, user_input: dict | None = None
    ) -> _FlowResultT:
        """Continue a data entry flow."""
        if (flow := self._progress.get(flow_id)) is None:
            raise UnknownFlow

        cur_step = flow.cur_step
        assert cur_step is not None

        if (
            data_schema := cur_step.get("data_schema")
        ) is not None and user_input is not None:
            data_schema = cast(vol.Schema, data_schema)
            try:
                user_input = data_schema(user_input)
            except vol.Invalid as ex:
                raised_errors = [ex]
                if isinstance(ex, vol.MultipleInvalid):
                    raised_errors = ex.errors

                schema_errors: dict[str, Any] = {}
                for error in raised_errors:
                    try:
                        _map_error_to_schema_errors(schema_errors, error, data_schema)
                    except ValueError:
                        # If we get here, the path in the exception does not exist in the schema.
                        schema_errors.setdefault("base", []).append(str(error))
                raise InvalidData(
                    "Schema validation failed",
                    path=ex.path,
                    error_message=ex.error_message,
                    schema_errors=schema_errors,
                ) from ex

        # Handle a menu navigation choice
        if cur_step["type"] == FlowResultType.MENU and user_input:
            result = await self._async_handle_step(
                flow, user_input["next_step_id"], None
            )
        else:
            result = await self._async_handle_step(
                flow, cur_step["step_id"], user_input
            )

        if cur_step["type"] in (
            FlowResultType.EXTERNAL_STEP,
            FlowResultType.SHOW_PROGRESS,
        ):
            if cur_step["type"] == FlowResultType.EXTERNAL_STEP and result[
                "type"
            ] not in (
                FlowResultType.EXTERNAL_STEP,
                FlowResultType.EXTERNAL_STEP_DONE,
            ):
                raise ValueError(
                    "External step can only transition to "
                    "external step or external step done."
                )
            if cur_step["type"] == FlowResultType.SHOW_PROGRESS and result[
                "type"
            ] not in (
                FlowResultType.SHOW_PROGRESS,
                FlowResultType.SHOW_PROGRESS_DONE,
            ):
                raise ValueError(
                    "Show progress can only transition to show progress or show"
                    " progress done."
                )

            # If the result has changed from last result, fire event to update
            # the frontend. The result is considered to have changed if:
            # - The step has changed
            # - The step is same but result type is SHOW_PROGRESS and progress_action
            #   or description_placeholders has changed
            if cur_step["step_id"] != result.get("step_id") or (
                result["type"] == FlowResultType.SHOW_PROGRESS
                and (
                    cur_step["progress_action"] != result.get("progress_action")
                    or cur_step["description_placeholders"]
                    != result.get("description_placeholders")
                )
            ):
                flow.async_notify_flow_changed()

        return result