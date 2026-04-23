def validate_root_path(cls, value: Any) -> str:
        if value is None:
            return ""
        if not isinstance(value, str):
            msg = "root_path must be a string"
            raise TypeError(msg)

        value = value.strip()
        if not value or value == "/":
            return ""

        if "://" in value or "?" in value or "#" in value:
            msg = "root_path must be an ASGI path prefix only, without scheme, query string, or fragment"
            raise ValueError(msg)

        if not value.startswith("/"):
            value = f"/{value}"

        return value.rstrip("/")