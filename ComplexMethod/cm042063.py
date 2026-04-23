def format_value(value, context: Context):
        """Fill parameters inside `value` with `options`."""
        if not isinstance(value, str):
            return value
        if "{" not in value:
            return value

        options = context.config.model_dump()
        for k, v in context.kwargs:
            options[k] = v  # None value is allowed to override and disable the value from config.
        opts = {k: v for k, v in options.items() if v is not None}
        try:
            return value.format(**opts)
        except KeyError as e:
            logger.warning(f"Parameter is missing:{e}")

        for k, v in opts.items():
            value = value.replace("{" + f"{k}" + "}", str(v))
        return value