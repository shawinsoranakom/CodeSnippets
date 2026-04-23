def replace_time(match) -> str:
    """
    Args:
        match (re.Match)
    Returns:
        str
    """

    is_range = len(match.groups()) > 5

    hour = match.group(1)
    minute = match.group(2)
    second = match.group(4)

    if is_range:
        hour_2 = match.group(6)
        minute_2 = match.group(7)
        second_2 = match.group(9)

    result = f"{num2str(hour)}点"
    if minute.lstrip("0"):
        if int(minute) == 30:
            result += "半"
        else:
            result += f"{_time_num2str(minute)}分"
    if second and second.lstrip("0"):
        result += f"{_time_num2str(second)}秒"

    if is_range:
        result += "至"
        result += f"{num2str(hour_2)}点"
        if minute_2.lstrip("0"):
            if int(minute) == 30:
                result += "半"
            else:
                result += f"{_time_num2str(minute_2)}分"
        if second_2 and second_2.lstrip("0"):
            result += f"{_time_num2str(second_2)}秒"

    return result