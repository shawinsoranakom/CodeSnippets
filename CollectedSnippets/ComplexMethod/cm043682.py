def validate_interval(cls, v):  # pylint: disable=R0911
        """Validate the interval to be valid for the TMX request."""
        if v is None or v == "day":
            return "day"
        if v in ("1M", "1mo", "month"):
            return "month"
        if "m" in v:
            return int(v.replace("m", ""))
        if "h" in v:
            return int(v.replace("h", "")) * 60
        if v == "1d":
            return "day"
        if v in ("1W", "1w", "week"):
            return "week"
        if v.isnumeric():
            return int(v)
        raise OpenBBError(f"Invalid interval: {v}")