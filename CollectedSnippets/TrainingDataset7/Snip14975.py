def get_formats():
    """Return all formats strings required for i18n to work."""
    FORMAT_SETTINGS = (
        "DATE_FORMAT",
        "DATETIME_FORMAT",
        "TIME_FORMAT",
        "YEAR_MONTH_FORMAT",
        "MONTH_DAY_FORMAT",
        "SHORT_DATE_FORMAT",
        "SHORT_DATETIME_FORMAT",
        "FIRST_DAY_OF_WEEK",
        "DECIMAL_SEPARATOR",
        "THOUSAND_SEPARATOR",
        "NUMBER_GROUPING",
        "DATE_INPUT_FORMATS",
        "TIME_INPUT_FORMATS",
        "DATETIME_INPUT_FORMATS",
    )
    return {attr: get_format(attr) for attr in FORMAT_SETTINGS}