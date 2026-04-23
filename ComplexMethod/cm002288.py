def check_codes_match(observed_code: str, theoretical_code: str) -> int | None:
    """
    Checks if two version of a code match with the exception of the class/function name.

    Args:
        observed_code (`str`): The code found.
        theoretical_code (`str`): The code to match.

    Returns:
        `Optional[int]`: The index of the first line where there is a difference (if any) and `None` if the codes
        match.
    """
    observed_code_header = observed_code.split("\n")[0]
    theoretical_code_header = theoretical_code.split("\n")[0]

    # Catch the function/class name: it is expected that those do not match.
    _re_class_match = re.compile(r"class\s+([^\(:]+)(?:\(|:)")
    _re_func_match = re.compile(r"def\s+([^\(]+)\(")
    for re_pattern in [_re_class_match, _re_func_match]:
        if re_pattern.match(observed_code_header) is not None:
            try:
                observed_obj_name = re_pattern.search(observed_code_header).groups()[0]
            except Exception:
                raise ValueError(
                    "Tried to split a class or function. It did not work. Error comes from: \n```\n"
                    + observed_code_header
                    + "\n```\n"
                )

            try:
                theoretical_name = re_pattern.search(theoretical_code_header).groups()[0]
            except Exception:
                raise ValueError(
                    "Tried to split a class or function. It did not work. Error comes from: \n```\n"
                    + theoretical_code_header
                    + "\n```\n"
                )
            theoretical_code_header = theoretical_code_header.replace(theoretical_name, observed_obj_name)

    # Find the first diff. Line 0 is special since we need to compare with the function/class names ignored.
    diff_index = 0
    if theoretical_code_header != observed_code_header:
        return 0

    diff_index = 1
    for observed_line, theoretical_line in zip(observed_code.split("\n")[1:], theoretical_code.split("\n")[1:]):
        if observed_line != theoretical_line:
            return diff_index
        diff_index += 1