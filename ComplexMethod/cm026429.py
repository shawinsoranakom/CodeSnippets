def convert(result: Any) -> list[int] | None:
        if template_validators.check_result_for_none(result):
            return None

        if isinstance(result, str):
            with contextlib.suppress(ValueError):
                result = _string_to_list(result)

        if (
            isinstance(result, (list, tuple))
            and len(result) == 2
            and all(isinstance(value, (int, float)) for value in result)
        ):
            hue, saturation = result
            if not (0 <= hue <= 360) or not (0 <= saturation <= 100):
                template_validators.log_validation_result_error(
                    entity,
                    CONF_HS,
                    result,
                    (
                        "expected a hue value between 0 and 360 and "
                        "a saturation value between 0 and 100: (0-360, 0-100)"
                    ),
                )
                return None

            return list(result)

        template_validators.log_validation_result_error(
            entity,
            CONF_HS,
            result,
            "expected a list of numbers: (0-360, 0-100)",
        )
        return None