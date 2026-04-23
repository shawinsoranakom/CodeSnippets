def _gather_info(fields) -> dict:
    """Gather info from user."""
    answers = {}

    for key, info in fields.items():
        hint = None
        while key not in answers:
            if hint is not None:
                print()
                print(f"Error: {hint}")

            try:
                print()
                msg = info["prompt"]
                if "default" in info:
                    msg += f" [{info['default']}]"
                value = input(f"{msg}\n> ")
            except (KeyboardInterrupt, EOFError) as err:
                raise ExitApp("Interrupted!", 1) from err

            value = value.strip()

            if value == "" and "default" in info:
                value = info["default"]

            hint = None

            for validator_hint, validator in info["validators"]:
                if not validator(value):
                    hint = validator_hint
                    break

            if hint is None:
                if "converter" in info:
                    value = info["converter"](value)
                answers[key] = value

    return answers