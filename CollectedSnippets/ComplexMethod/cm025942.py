def _get_expose_value(
        self, state: State | None, option: KnxExposeOptions
    ) -> bool | int | float | str | None:
        """Extract value from state for a specific option."""
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            if option.default is None:
                return None
            value = option.default
        elif option.attribute is not None:
            _attr = state.attributes.get(option.attribute)
            value = _attr if _attr is not None else option.default
        else:
            value = state.state

        if option.value_template is not None:
            try:
                value = option.value_template.async_render_with_possible_json_value(
                    value, error_value=None
                )
            except (TemplateError, TypeError, ValueError) as err:
                _LOGGER.warning(
                    "Error rendering value template for KNX expose %s %s %s: %s",
                    self.entity_id,
                    option.attribute or "state",
                    option.value_template.template,
                    err,
                )
                return None

        if issubclass(option.dpt, DPT1BitEnum):
            if value in (1, STATE_ON, "True"):
                return True
            if value in (0, STATE_OFF, "False"):
                return False

        # Handle numeric and string DPT conversions
        if value is not None:
            try:
                if issubclass(option.dpt, DPTNumeric):
                    return float(value)
                if issubclass(option.dpt, DPTString):
                    # DPT 16.000 only allows up to 14 Bytes
                    return str(value)[:14]
            except (ValueError, TypeError) as err:
                _LOGGER.warning(
                    'Could not expose %s %s value "%s" to KNX: Conversion failed: %s',
                    self.entity_id,
                    option.attribute or "state",
                    value,
                    err,
                )
                return None
        return value