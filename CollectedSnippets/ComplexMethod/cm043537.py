def parse_and_split_input(an_input: str, custom_filters: list) -> list[str]:
    """Filter and split the input queue.

    Uses regex to filters command arguments that have forward slashes so that it doesn't
    break the execution of the command queue.
    Currently handles unix paths and sorting settings for screener menus.

    Parameters
    ----------
    an_input : str
        User input as string
    custom_filters : List
        Additional regular expressions to match

    Returns
    -------
    List[str]
        Command queue as list
    """
    # Make sure that the user can go back to the root when doing "/"
    if an_input and an_input == "/":
        an_input = "home"

    # everything from ` -f ` to the next known extension
    file_flag = r"(\ -f |\ --file )"
    up_to = r".*?"
    known_extensions = r"(\.(xlsx|csv|xls|tsv|json|yaml|ini|openbb|ipynb))"
    unix_path_arg_exp = f"({file_flag}{up_to}{known_extensions})"

    # Add custom expressions to handle edge cases of individual controllers
    custom_filter = ""
    for exp in custom_filters:
        if exp is not None:
            custom_filter += f"|{exp}"
            del exp

    slash_filter_exp = f"({unix_path_arg_exp}){custom_filter}"

    filter_input = True
    placeholders: dict[str, str] = {}
    while filter_input:
        match = re.search(pattern=slash_filter_exp, string=an_input)
        if match is not None:
            placeholder = f"{{placeholder{len(placeholders) + 1}}}"
            placeholders[placeholder] = an_input[
                match.span()[0] : match.span()[1]
            ]  # noqa:E203
            an_input = (
                an_input[: match.span()[0]] + placeholder + an_input[match.span()[1] :]
            )  # noqa:E203
        else:
            filter_input = False

    commands = an_input.split("/") if "timezone" not in an_input else [an_input]

    for command_num, command in enumerate(commands):
        if command == commands[-1] == "":
            return list(filter(None, commands))
        matching_placeholders = [tag for tag in placeholders if tag in command]
        if len(matching_placeholders) > 0:
            for tag in matching_placeholders:
                commands[command_num] = command.replace(tag, placeholders[tag])
    return commands