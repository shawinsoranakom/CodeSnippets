def validate_custom_dates(user_input: dict[str, Any]) -> None:
    """Validate custom dates for add/remove holidays."""
    for add_date in user_input[CONF_ADD_HOLIDAYS]:
        if (
            not _is_valid_date_range(add_date, AddDateRangeError)
            and dt_util.parse_date(add_date) is None
        ):
            raise AddDatesError("Incorrect date")

    year: int = dt_util.now().year
    if country := user_input.get(CONF_COUNTRY):
        language: str | None = user_input.get(CONF_LANGUAGE)
        province = user_input.get(CONF_PROVINCE)
        obj_holidays = country_holidays(
            country=country,
            subdiv=province,
            years=year,
            language=language,
            categories=[PUBLIC, *user_input.get(CONF_CATEGORY, [])],
        )

    else:
        obj_holidays = HolidayBase(years=year)

    for remove_date in user_input[CONF_REMOVE_HOLIDAYS]:
        if (
            not _is_valid_date_range(remove_date, RemoveDateRangeError)
            and dt_util.parse_date(remove_date) is None
            and obj_holidays.get_named(remove_date) == []
        ):
            raise RemoveDatesError("Incorrect date or name")