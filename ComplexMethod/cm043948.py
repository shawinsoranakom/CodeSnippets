def parse_time_period(time_str: str) -> str:
    """Convert IMF time period formats to valid date strings (period ending).

    Examples:
        '2025-M03' -> '2025-03-31'
        '2025-Q1' -> '2025-03-31'
        '2025' -> '2025-12-31'
    """
    # pylint: disable=import-outside-toplevel
    import calendar
    from datetime import datetime

    if not time_str:
        return time_str

    try:
        # Handle monthly format (YYYY-MXX)
        if "-M" in time_str:
            parts = time_str.split("-M")
            if len(parts) == 2:
                year = int(parts[0])
                month = int(parts[1])

                # Get the last day of the month using calendar module
                last_day = calendar.monthrange(year, month)[1]

                # Create date object and format it
                date_obj = datetime(year, month, last_day)
                return date_obj.strftime("%Y-%m-%d")

        # Handle quarterly format (YYYY-QX)
        elif "-Q" in time_str:
            parts = time_str.split("-Q")
            if len(parts) == 2:
                year = int(parts[0])
                quarter = int(parts[1])

                # Map quarters to their last month
                quarter_last_month = {1: 3, 2: 6, 3: 9, 4: 12}
                month = quarter_last_month.get(quarter, 12)

                # Get the last day of the quarter's last month
                last_day = calendar.monthrange(year, month)[1]

                # Create date object and format it
                date_obj = datetime(year, month, last_day)
                return date_obj.strftime("%Y-%m-%d")

        # Handle yearly format (YYYY)
        elif len(time_str) == 4 and time_str.isdigit():
            year = int(time_str)
            # Last day of the year is always December 31
            date_obj = datetime(year, 12, 31)
            return date_obj.strftime("%Y-%m-%d")

        # Return as-is if it's already in a valid format or unrecognized
        return time_str

    except (ValueError, KeyError):
        # If parsing fails, return the original string
        return time_str