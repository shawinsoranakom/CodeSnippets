def convert(result: Any) -> float | int | None:
        if check_result_for_none(result, **kwargs):
            return None

        if (result_type := type(result)) is bool:
            log_validation_result_error(entity, attribute, result, message)
            return None

        if isinstance(result, (float, int)):
            value = result
            if return_type is int and result_type is float:
                value = int(value)
            elif return_type is float and result_type is int:
                value = float(value)
        else:
            try:
                value = vol.Coerce(float)(result)
                if return_type is int:
                    value = int(value)
            except vol.Invalid:
                log_validation_result_error(entity, attribute, result, message)
                return None

        if minimum is None and maximum is None:
            return value

        if (
            (
                minimum is not None
                and maximum is not None
                and minimum <= value <= maximum
            )
            or (minimum is not None and maximum is None and value >= minimum)
            or (minimum is None and maximum is not None and value <= maximum)
        ):
            return value

        log_validation_result_error(entity, attribute, result, message)
        return None