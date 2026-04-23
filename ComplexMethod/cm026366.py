def async_calculate_period(
    duration: datetime.timedelta | None,
    start_template: Template | None,
    end_template: Template | None,
    log_errors: bool = True,
) -> tuple[datetime.datetime, datetime.datetime]:
    """Parse the templates and return the period."""
    bounds: dict[str, datetime.datetime | None] = {
        DURATION_START: None,
        DURATION_END: None,
    }
    for bound, template in (
        (DURATION_START, start_template),
        (DURATION_END, end_template),
    ):
        # Parse start
        if template is None:
            continue
        try:
            rendered = template.async_render(
                log_fn=None if log_errors else lambda *args, **kwargs: None
            )
        except (TemplateError, TypeError) as ex:
            if (
                log_errors
                and ex.args
                and not ex.args[0].startswith("UndefinedError: 'None' has no attribute")
            ):
                _LOGGER.error("Error parsing template for field %s", bound, exc_info=ex)
            raise type(ex)(f"Error parsing template for field {bound}: {ex}") from ex
        if isinstance(rendered, str):
            bounds[bound] = dt_util.parse_datetime(rendered)
        if bounds[bound] is not None:
            continue
        try:
            bounds[bound] = dt_util.as_local(
                dt_util.utc_from_timestamp(math.floor(float(rendered)))
            )
        except ValueError as ex:
            raise ValueError(
                f"Parsing error: {bound} must be a datetime or a timestamp: {ex}"
            ) from ex

    start = bounds[DURATION_START]
    end = bounds[DURATION_END]

    # Calculate start or end using the duration
    if start is None:
        assert end is not None
        assert duration is not None
        start = end - duration
    if end is None:
        assert start is not None
        assert duration is not None
        end = start + duration

    return start, end