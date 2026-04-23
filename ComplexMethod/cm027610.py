async def _show_next_step(
        self,
        next_step_id: str,
        error: SchemaFlowError | None = None,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Show form for next step."""
        if isinstance(self._flow[next_step_id], SchemaFlowMenuStep):
            menu_step = cast(SchemaFlowMenuStep, self._flow[next_step_id])
            return self._handler.async_show_menu(
                step_id=next_step_id,
                menu_options=await self._get_options(menu_step),
                sort=menu_step.sort,
            )

        form_step = cast(SchemaFlowFormStep, self._flow[next_step_id])

        if (data_schema := await self._get_schema(form_step)) is None:
            return await self._show_next_step_or_create_entry(form_step)

        description_placeholders: dict[str, str] | None = None
        if form_step.description_placeholders is not UNDEFINED:
            description_placeholders = await form_step.description_placeholders(self)

        suggested_values: dict[str, Any] = {}
        if form_step.suggested_values is UNDEFINED:
            suggested_values = self._options
        elif form_step.suggested_values:
            suggested_values = await form_step.suggested_values(self)

        if user_input:
            # We don't want to mutate the existing options
            suggested_values = copy.deepcopy(suggested_values)
            self._update_and_remove_omitted_optional_keys(
                suggested_values, user_input, await self._get_schema(form_step)
            )

        if data_schema.schema:
            # Make a copy of the schema with suggested values set to saved options
            data_schema = self._handler.add_suggested_values_to_schema(
                data_schema, suggested_values
            )

        errors = {"base": str(error)} if error else None

        # Show form for next step
        last_step = None
        if not callable(form_step.next_step):
            last_step = form_step.next_step is None
        return self._handler.async_show_form(
            step_id=next_step_id,
            data_schema=data_schema,
            description_placeholders=description_placeholders,
            errors=errors,
            last_step=last_step,
            preview=form_step.preview,
        )