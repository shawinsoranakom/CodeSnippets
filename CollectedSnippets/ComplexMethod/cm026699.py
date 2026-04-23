def get_holidays_object(
    country: str | None,
    province: str | None,
    year: int,
    language: str | None,
    categories: list[str] | None,
) -> HolidayBase:
    """Get the object for the requested country and year."""
    if not country:
        return HolidayBase()

    set_categories = None
    if categories:
        category_list = [PUBLIC]
        category_list.extend(categories)
        set_categories = tuple(category_list)

    obj_holidays: HolidayBase = country_holidays(
        country,
        subdiv=province,
        years=[year, year + 1],
        language=language,
        categories=set_categories,
    )

    supported_languages = obj_holidays.supported_languages
    default_language = obj_holidays.default_language

    if default_language and not language:
        # If no language is set, use the default language
        LOGGER.debug("Changing language from None to %s", default_language)
        return country_holidays(  # Return default if no language
            country,
            subdiv=province,
            years=year,
            language=default_language,
            categories=set_categories,
        )

    if (
        default_language
        and language
        and language not in supported_languages
        and language.startswith("en")
    ):
        # If language does not match supported languages, use the first English variant
        if default_language.startswith("en"):
            LOGGER.debug("Changing language from %s to %s", language, default_language)
            return country_holidays(  # Return default English if default language
                country,
                subdiv=province,
                years=year,
                language=default_language,
                categories=set_categories,
            )
        for lang in supported_languages:
            if lang.startswith("en"):
                LOGGER.debug("Changing language from %s to %s", language, lang)
                return country_holidays(
                    country,
                    subdiv=province,
                    years=year,
                    language=lang,
                    categories=set_categories,
                )

    if default_language and language and language not in supported_languages:
        # If language does not match supported languages, use the default language
        LOGGER.debug("Changing language from %s to %s", language, default_language)
        return country_holidays(  # Return default English if default language
            country,
            subdiv=province,
            years=year,
            language=default_language,
            categories=set_categories,
        )

    return obj_holidays