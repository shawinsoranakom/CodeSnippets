def append_date_time_to_string(input_string: str) -> str:
    """Append datetime string to input string.
    Returns datetime string if input is empty string.
    """
    now = datetime.now()

    if not input_string:
        return now.strftime("%Y-%m-%d_%H-%M-%S")
    else:
        return f'{input_string}_{now.strftime("%Y-%m-%d_%H-%M-%S")}'