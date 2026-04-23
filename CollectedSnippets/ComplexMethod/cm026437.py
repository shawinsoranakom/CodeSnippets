def convert(result: Any) -> T | None:
        if check_result_for_none(result, **kwargs):
            return None

        if isinstance(result, str):
            value = result.lower().strip()
            try:
                return state_enum(value)
            except ValueError:
                pass

        if state_on or state_off:
            try:
                bool_value = cv.boolean(result)
                if state_on and bool_value:
                    return state_on

                if state_off and not bool_value:
                    return state_off

            except vol.Invalid:
                pass

        expected = tuple(s.value for s in state_enum)
        if state_on:
            expected += RESULT_ON
        if state_off:
            expected += RESULT_OFF

        log_validation_result_error(
            entity,
            attribute,
            result,
            expected,
        )
        return None