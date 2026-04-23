def wilight_to_hass_trigger(value: str | None) -> str | None:
    """Convert wilight trigger to hass description.

    Ex: "12719001" -> "sun mon tue wed thu fri sat 19:00 On"
        "00000000" -> "00:00 Off"
    """
    if value is None:
        return value

    locale.setlocale(locale.LC_ALL, "")
    week_days = list(calendar.day_abbr)
    days = bin(int(value[0:3]))[2:].zfill(8)
    desc = ""
    if int(days[7:8]) == 1:
        desc += f"{week_days[6]} "
    if int(days[6:7]) == 1:
        desc += f"{week_days[0]} "
    if int(days[5:6]) == 1:
        desc += f"{week_days[1]} "
    if int(days[4:5]) == 1:
        desc += f"{week_days[2]} "
    if int(days[3:4]) == 1:
        desc += f"{week_days[3]} "
    if int(days[2:3]) == 1:
        desc += f"{week_days[4]} "
    if int(days[1:2]) == 1:
        desc += f"{week_days[5]} "
    desc += f"{value[3:5]}:{value[5:7]} "
    if int(value[7:8]) == 1:
        desc += "On"
    else:
        desc += "Off"

    return desc