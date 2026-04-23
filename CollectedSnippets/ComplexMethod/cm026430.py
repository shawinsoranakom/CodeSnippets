def convert(result: Any) -> list[int] | None:
        if template_validators.check_result_for_none(result):
            return None

        if isinstance(result, str):
            with contextlib.suppress(ValueError):
                result = _string_to_list(result)

        if (
            isinstance(result, (list, tuple))
            and len(result) == length
            and all(isinstance(value, (int, float)) for value in result)
        ):
            # Ensure the result are numbers between 0 and 255.
            if all(0 <= value <= 255 for value in result):
                return list(result)

        template_validators.log_validation_result_error(
            entity, attribute, result, message
        )
        return None