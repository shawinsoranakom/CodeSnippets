def _warn_deprecated_options(self):
        if self['http_enable'] and not self.http_socket_activation:
            for map_ in self.options.maps:
                if 'http_interface' in map_:
                    if map_ is self._file_options and map_['http_interface'] == '':  # noqa: PLC1901
                        del map_['http_interface']
                    elif map_ is self._default_options:
                        self._log(logging.WARNING, "missing %s, using 0.0.0.0 by default, will change to 127.0.0.1 in 20.0", self.options_index['http_interface'])
                    else:
                        break

        for old_option_name, new_option_name in self.aliases.items():
            for source_name, deprecated_value in self._get_sources(old_option_name).items():
                if deprecated_value is EMPTY:
                    continue
                default_value = self._default_options[new_option_name]
                current_value = self[new_option_name]

                if deprecated_value in (current_value, default_value):
                    # Surely this is from a --save that was run in a
                    # prior version. There is no point in emitting a
                    # warning because: (1) it holds the same value as
                    # the correct option, and (2) it is going to be
                    # automatically removed on the next --save anyway.
                    self._log(logging.INFO,
                        f"The {old_option_name!r} option found in the "
                        f"{source_name} is a deprecated alias to "
                        f"{new_option_name!r}. The configuration value "
                        "is the same as the default value, it can "
                        "safely be removed.")
                elif current_value == default_value:
                    # deprecated_value != current_value == default_value
                    # assume the new option was not set
                    self._runtime_options[new_option_name] = self.parse(new_option_name, deprecated_value)
                    self._warn(
                        f"The {old_option_name!r} option found in the "
                        f"{source_name} is a deprecated alias to "
                        f"{new_option_name!r}, please use the latter.",
                        DeprecationWarning)
                else:
                    # deprecated_value != current_value != default_value
                    self.parser.error(
                        f"The two options {old_option_name!r} "
                        f"(found in the {source_name} but deprecated) "
                        f"and {new_option_name!r} are set to different "
                        "values. Please remove the first one and make "
                        "sure the second is correct."
                    )