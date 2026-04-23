def async_setup(
        self,
        strict: bool = False,
        log_fn: Callable[[int, str], None] | None = None,
    ) -> None:
        """Activation of template tracking."""
        block_render = False
        super_template = self._track_templates[0] if self._has_super_template else None

        # Render the super template first
        if super_template is not None:
            template = super_template.template
            variables = super_template.variables
            self._info[template] = info = template.async_render_to_info(
                variables, strict=strict, log_fn=log_fn
            )

            # If the super template did not render to True, don't update other templates
            try:
                super_result: str | TemplateError = info.result()
            except TemplateError as ex:
                super_result = ex
            if (
                super_result is not None
                and self._super_template_as_boolean(super_result) is not True
            ):
                block_render = True

        # Then update the remaining templates unless blocked by the super template
        for track_template_ in self._track_templates:
            if block_render or track_template_ == super_template:
                continue
            template = track_template_.template
            variables = track_template_.variables
            self._info[template] = info = template.async_render_to_info(
                variables, strict=strict, log_fn=log_fn
            )

            if info.exception:
                if not log_fn:
                    _LOGGER.error(
                        "Error while processing template: %s",
                        track_template_.template,
                        exc_info=info.exception,
                    )
                else:
                    log_fn(logging.ERROR, str(info.exception))

        self._track_state_changes = async_track_state_change_filtered(
            self.hass, _render_infos_to_track_states(self._info.values()), self._refresh
        )
        self._update_time_listeners()
        _LOGGER.debug(
            (
                "Template group %s listens for %s, first render blocked by super"
                " template: %s"
            ),
            self._track_templates,
            self.listeners,
            block_render,
        )