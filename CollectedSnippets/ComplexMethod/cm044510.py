def _selected_to_choices(self):
        """ dict: The selected value and valid choices for multi-option, radio or combo options.
        """
        valid_choices = {cmd: {opt: {"choices": val.cpanel_option.choices,
                                     "is_multi": val.cpanel_option.is_multi_option}
                               for opt, val in data.items()
                               if hasattr(val, "cpanel_option")  # Filter out helptext
                               and val.cpanel_option.choices is not None
                               }
                         for cmd, data in self._config.cli_opts.opts.items()}
        logger.trace("valid_choices: %s", valid_choices)
        retval = {command: {option: {"value": value,
                                     "is_multi": valid_choices[command][option]["is_multi"],
                                     "choices":  valid_choices[command][option]["choices"]}
                            for option, value in options.items()
                            if value and command in valid_choices
                            and option in valid_choices[command]}
                  for command, options in self._options.items()
                  if isinstance(options, dict)}
        logger.trace("returning: %s", retval)
        return retval