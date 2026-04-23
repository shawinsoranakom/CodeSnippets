def validator(config: dict) -> dict:
        """Check if key is in config and log warning or error."""
        if key in config:
            if option_removed:
                level = logging.ERROR
                option_status = "has been removed"
            else:
                level = logging.WARNING
                option_status = "is deprecated"

            try:
                near = (
                    f"near {config.__config_file__}"  # type: ignore[attr-defined]
                    f":{config.__line__} "  # type: ignore[attr-defined]
                )
            except AttributeError:
                near = ""
            arguments: tuple[str, ...]
            if replacement_key:
                warning = "The '%s' option %s%s, please replace it with '%s'"
                arguments = (key, near, option_status, replacement_key)
            else:
                warning = (
                    "The '%s' option %s%s, please remove it from your configuration"
                )
                arguments = (key, near, option_status)

            if raise_if_present:
                raise vol.Invalid(warning % arguments)

            get_integration_logger(__name__).log(level, warning, *arguments)
            value = config[key]
            if replacement_key or option_removed:
                config.pop(key)
        else:
            value = default

        keys = [key]
        if replacement_key:
            keys.append(replacement_key)
            if value is not None and (
                replacement_key not in config or default == config.get(replacement_key)
            ):
                config[replacement_key] = value

        return has_at_most_one_key(*keys)(config)