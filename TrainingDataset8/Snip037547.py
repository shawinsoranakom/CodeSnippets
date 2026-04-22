def parse_value(value: Value) -> str:
        if value is None:
            return "—"
        if isinstance(value, int) or isinstance(value, float) or isinstance(value, str):
            return str(value)
        elif hasattr(value, "item"):
            # Add support for numpy values (e.g. int16, float64, etc.)
            try:
                # Item could also be just a variable, so we use try, except
                if isinstance(value.item(), float) or isinstance(value.item(), int):
                    return str(value.item())
            except Exception:
                # If the numpy item is not a valid value, the TypeError below will be raised.
                pass

        raise TypeError(
            f"'{str(value)}' is of type {str(type(value))}, which is not an accepted type."
            " value only accepts: int, float, str, or None."
            " Please convert the value to an accepted type."
        )