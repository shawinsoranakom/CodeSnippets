def convert(result: Any) -> bool | None:
        if check_result_for_none(result, **kwargs):
            return None

        if isinstance(result, bool):
            return result

        if isinstance(result, str) and (as_true or as_false):
            value = result.lower().strip()
            if as_true and value in as_true:
                return True
            if as_false and value in as_false:
                return False

        try:
            return cv.boolean(result)
        except vol.Invalid:
            pass

        items: tuple[str, ...] = RESULT_ON + RESULT_OFF
        if as_true:
            items += as_true
        if as_false:
            items += as_false

        log_validation_result_error(entity, attribute, result, items)
        return None