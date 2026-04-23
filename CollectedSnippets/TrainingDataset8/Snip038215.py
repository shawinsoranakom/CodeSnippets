def page_sort_key(script_path: Path) -> Tuple[float, str]:
    matches = re.findall(PAGE_FILENAME_REGEX, script_path.name)

    # Failing this assert should only be possible if script_path isn't a Python
    # file, which should never happen.
    assert len(matches) > 0, f"{script_path} is not a Python file"

    [(number, label)] = matches
    label = label.lower()

    if number == "":
        return (float("inf"), label)

    return (float(number), label)