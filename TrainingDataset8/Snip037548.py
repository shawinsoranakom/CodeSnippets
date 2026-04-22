def parse_delta(delta: Delta) -> str:
        if delta is None or delta == "":
            return ""
        if isinstance(delta, str):
            return dedent(delta)
        elif isinstance(delta, int) or isinstance(delta, float):
            return str(delta)
        else:
            raise TypeError(
                f"'{str(delta)}' is of type {str(type(delta))}, which is not an accepted type."
                " delta only accepts: int, float, str, or None."
                " Please convert the value to an accepted type."
            )