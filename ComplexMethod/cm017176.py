def explain_query_prefix(self, format=None, **options):
        extra = {}
        if serialize := options.pop("serialize", None):
            if serialize.upper() in {"TEXT", "BINARY"}:
                extra["SERIALIZE"] = serialize.upper()
        # Normalize options.
        if options:
            options = {
                name.upper(): "true" if value else "false"
                for name, value in options.items()
            }
            for valid_option in self.explain_options:
                value = options.pop(valid_option, None)
                if value is not None:
                    extra[valid_option] = value
        prefix = super().explain_query_prefix(format, **options)
        if format:
            extra["FORMAT"] = format
        if extra:
            prefix += " (%s)" % ", ".join("%s %s" % i for i in extra.items())
        return prefix