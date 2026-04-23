def get_location_astral_event_next(
    location: astral.location.Location,
    elevation: astral.Elevation,
    event: str,
    utc_point_in_time: datetime.datetime | None = None,
    offset: datetime.timedelta | None = None,
) -> datetime.datetime:
    """Calculate the next specified solar event."""

    if offset is None:
        offset = datetime.timedelta()

    if utc_point_in_time is None:
        utc_point_in_time = dt_util.utcnow()

    kwargs: dict[str, Any] = {"local": False}
    if event not in ELEVATION_AGNOSTIC_EVENTS:
        kwargs["observer_elevation"] = elevation

    mod = -1
    first_err = None
    while mod < 367:
        try:
            next_dt = (
                cast(_AstralSunEventCallable, getattr(location, event))(
                    dt_util.as_local(utc_point_in_time).date()
                    + datetime.timedelta(days=mod),
                    **kwargs,
                )
                + offset
            )
            if next_dt > utc_point_in_time:
                return next_dt
        except ValueError as err:
            if not first_err:
                first_err = err
        mod += 1
    raise ValueError(
        f"Unable to find event after one year, initial ValueError: {first_err}"
    ) from first_err