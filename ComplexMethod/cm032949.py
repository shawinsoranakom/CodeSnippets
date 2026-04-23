def datetime_from_string(datetime_string: str) -> datetime:
    datetime_string = datetime_string.strip()

    match_jira_format = _TZ_SUFFIX_PATTERN.search(datetime_string)
    if match_jira_format:
        sign, tz_field = match_jira_format.groups()
        digits = tz_field.replace(":", "")

        if digits.isdigit() and 1 <= len(digits) <= 4:
            if len(digits) >= 3:
                hours = digits[:-2].rjust(2, "0")
                minutes = digits[-2:]
            else:
                hours = digits.rjust(2, "0")
                minutes = "00"

            normalized = f"{sign}{hours}:{minutes}"
            datetime_string = f"{datetime_string[: match_jira_format.start()]}{normalized}"

    # Handle the case where the datetime string ends with 'Z' (Zulu time)
    if datetime_string.endswith("Z"):
        datetime_string = datetime_string[:-1] + "+00:00"

    # Handle timezone format "+0000" -> "+00:00"
    if datetime_string.endswith("+0000"):
        datetime_string = datetime_string[:-5] + "+00:00"

    datetime_object = datetime.fromisoformat(datetime_string)

    if datetime_object.tzinfo is None:
        # If no timezone info, assume it is UTC
        datetime_object = datetime_object.replace(tzinfo=timezone.utc)
    else:
        # If not in UTC, translate it
        datetime_object = datetime_object.astimezone(timezone.utc)

    return datetime_object