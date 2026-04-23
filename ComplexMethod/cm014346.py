def __getattr__(self, name: str) -> Any:
        try:
            config = self._config[name]

            if config.hide:
                raise AttributeError(f"{self.__name__}.{name} does not exist")

            # Issue deprecation warning on read (once per config)
            self._warn_if_deprecated(name, config)

            alias_val = self._get_alias_val(config)
            if alias_val is not _UNSET_SENTINEL:
                return alias_val

            if config.env_value_force is not _UNSET_SENTINEL:
                return config.env_value_force

            user_override = config.user_override.get()
            if user_override is not _UNSET_SENTINEL:
                return user_override

            if config.env_value_default is not _UNSET_SENTINEL:
                return config.env_value_default

            if config.justknob is not None:
                # JK only supports bools and ints
                return justknobs_check(name=config.justknob, default=config.default)

            # Reference types can still be modified, so copy them to
            # user_overrides to prevent accidental mutation of defaults.
            if not isinstance(config.default, _IMMUTABLE_CONFIG_TYPES):
                config.user_override.set(copy.deepcopy(config.default))
                return config.user_override.get()
            return config.default

        except KeyError as e:
            # make hasattr() work properly
            raise AttributeError(f"{self.__name__}.{name} does not exist") from e