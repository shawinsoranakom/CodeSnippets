async def _async_form_step(
        self, step_id: str, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a form step."""
        form_step: SchemaFlowFormStep = cast(SchemaFlowFormStep, self._flow[step_id])

        if (
            user_input is not None
            and (data_schema := await self._get_schema(form_step))
            and data_schema.schema
            and not self._handler.show_advanced_options
        ):
            # Add advanced field default if not set
            for key in data_schema.schema:
                if isinstance(key, (vol.Optional, vol.Required)):
                    if (
                        key.description
                        and key.description.get("advanced")
                        and key.default is not vol.UNDEFINED
                        and key not in self._options
                    ):
                        user_input[str(key.schema)] = cast(
                            Callable[[], Any], key.default
                        )()

        if user_input is not None and form_step.validate_user_input is not None:
            # Do extra validation of user input
            try:
                user_input = await form_step.validate_user_input(self, user_input)
            except SchemaFlowError as exc:
                return await self._show_next_step(step_id, exc, user_input)

        if user_input is not None:
            # User input was validated successfully, update options
            self._update_and_remove_omitted_optional_keys(
                self._options, user_input, data_schema
            )

        if user_input is not None or form_step.schema is None:
            return await self._show_next_step_or_create_entry(form_step)

        return await self._show_next_step(step_id)