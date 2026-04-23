def _get_dict(
        self,
        ignored_keys: list[str] | None = None,
        ignored_prefixes: list[str] | None = None,
        skip_default: bool = False,
    ) -> dict[str, Any]:
        """Export a dictionary of current configuration keys and values.

        This function is design to provide a single point which handles
        accessing config options and exporting them into a dictionary.
        This is used by a number of different user facing export methods
        which all have slightly different semantics re: how and what to
        skip.
        If a config is aliased, it skips this config.

        Arguments:
            ignored_keys are keys that should not be exported.
            ignored_prefixes are prefixes that if a key matches should
                not be exported
            skip_default does two things. One if a key has not been modified
                it skips it.
        """
        config: dict[str, Any] = {}
        for key, entry in self._config.items():
            if entry.alias is not None:
                continue
            if ignored_keys and key in ignored_keys:
                continue
            if ignored_prefixes:
                if any(key.startswith(prefix) for prefix in ignored_prefixes):
                    continue
            if skip_default and self._is_default(key):
                continue

            # Read value directly, bypassing __getattr__ overhead
            # (deprecation warnings, alias resolution).
            user_override = entry.user_override.get()
            if entry.env_value_force is not _UNSET_SENTINEL:
                val = entry.env_value_force
            elif user_override is not _UNSET_SENTINEL:
                val = user_override
            elif entry.env_value_default is not _UNSET_SENTINEL:
                val = entry.env_value_default
            elif entry.justknob is not None:
                val = justknobs_check(name=entry.justknob, default=entry.default)
            else:
                val = entry.default
            if not isinstance(val, _IMMUTABLE_CONFIG_TYPES):
                val = copy.deepcopy(val)
            config[key] = val

        return config