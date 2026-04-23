def parse_generate_flags(generate_flags: list[str] | None) -> dict:
    """Parses the generate flags from the user input into a dictionary of `generate` kwargs."""
    if generate_flags is None or len(generate_flags) == 0:
        return {}

    # Assumption: `generate_flags` is a list of strings, each string being a `flag=value` pair, that can be parsed
    # into a json string if we:
    # 1. Add quotes around each flag name
    generate_flags_as_dict = {'"' + flag.split("=")[0] + '"': flag.split("=")[1] for flag in generate_flags}

    # 2. Handle types:
    # 2. a. booleans should be lowercase, None should be null
    generate_flags_as_dict = {
        k: v.lower() if v.lower() in ["true", "false"] else v for k, v in generate_flags_as_dict.items()
    }
    generate_flags_as_dict = {k: "null" if v == "None" else v for k, v in generate_flags_as_dict.items()}

    # 2. b. strings should be quoted
    def is_number(s: str) -> bool:
        # handle negative numbers
        s = s.removeprefix("-")
        return s.replace(".", "", 1).isdigit()

    generate_flags_as_dict = {k: f'"{v}"' if not is_number(v) else v for k, v in generate_flags_as_dict.items()}
    # 2. c. [no processing needed] lists are lists of ints because `generate` doesn't take lists of strings :)
    # We also mention in the help message that we only accept lists of ints for now.

    # 3. Join the result into a comma separated string
    generate_flags_string = ", ".join([f"{k}: {v}" for k, v in generate_flags_as_dict.items()])

    # 4. Add the opening/closing brackets
    generate_flags_string = "{" + generate_flags_string + "}"

    # 5. Remove quotes around boolean/null and around lists
    generate_flags_string = generate_flags_string.replace('"null"', "null")
    generate_flags_string = generate_flags_string.replace('"true"', "true")
    generate_flags_string = generate_flags_string.replace('"false"', "false")
    generate_flags_string = generate_flags_string.replace('"[', "[")
    generate_flags_string = generate_flags_string.replace(']"', "]")

    # 6. Replace the `=` with `:`
    generate_flags_string = generate_flags_string.replace("=", ":")

    try:
        processed_generate_flags = json.loads(generate_flags_string)
    except json.JSONDecodeError:
        raise ValueError(
            "Failed to convert `generate_flags` into a valid JSON object."
            "\n`generate_flags` = {generate_flags}"
            "\nConverted JSON string = {generate_flags_string}"
        )
    return processed_generate_flags