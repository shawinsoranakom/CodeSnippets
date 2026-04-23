def add_remove_custom_holidays(
    hass: HomeAssistant,
    entry: WorkdayConfigEntry,
    country: str | None,
    calc_add_holidays: list[DateLike],
    calc_remove_holidays: list[str],
) -> None:
    """Add or remove custom holidays."""
    next_year = dt_util.now().year + 1

    # Add custom holidays
    try:
        entry.runtime_data.append(calc_add_holidays)
    except ValueError as error:
        LOGGER.error("Could not add custom holidays: %s", error)

    # Remove custom holidays
    for remove_holiday in calc_remove_holidays:
        try:
            # is this formatted as a date?
            if dt_util.parse_date(remove_holiday):
                # remove holiday by date
                removed = entry.runtime_data.pop(remove_holiday)
                LOGGER.debug("Removed %s", remove_holiday)
            else:
                # remove holiday by name
                LOGGER.debug("Treating '%s' as named holiday", remove_holiday)
                removed = entry.runtime_data.pop_named(remove_holiday)
                for holiday in removed:
                    LOGGER.debug("Removed %s by name '%s'", holiday, remove_holiday)
        except KeyError as unmatched:
            LOGGER.warning("No holiday found matching %s", unmatched)
            if _date := dt_util.parse_date(remove_holiday):
                if _date.year <= next_year:
                    # Only check and raise issues for max next year
                    async_create_issue(
                        hass,
                        DOMAIN,
                        f"bad_date_holiday-{entry.entry_id}-{slugify(remove_holiday)}",
                        is_fixable=True,
                        is_persistent=False,
                        severity=IssueSeverity.WARNING,
                        translation_key="bad_date_holiday",
                        translation_placeholders={
                            CONF_COUNTRY: country or "-",
                            "title": entry.title,
                            CONF_REMOVE_HOLIDAYS: remove_holiday,
                        },
                        data={
                            "entry_id": entry.entry_id,
                            "country": country,
                            "named_holiday": remove_holiday,
                        },
                    )
            else:
                async_create_issue(
                    hass,
                    DOMAIN,
                    f"bad_named_holiday-{entry.entry_id}-{slugify(remove_holiday)}",
                    is_fixable=True,
                    is_persistent=False,
                    severity=IssueSeverity.WARNING,
                    translation_key="bad_named_holiday",
                    translation_placeholders={
                        CONF_COUNTRY: country or "-",
                        "title": entry.title,
                        CONF_REMOVE_HOLIDAYS: remove_holiday,
                    },
                    data={
                        "entry_id": entry.entry_id,
                        "country": country,
                        "named_holiday": remove_holiday,
                    },
                )