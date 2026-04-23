def _check_valid_choices(self):
        """ Check whether the loaded file has any selected combo/radio/multi-option values that are
        no longer valid and remove them so that they are not passed into faceswap. """
        for command, options in self._selected_to_choices.items():
            for option, data in options.items():
                if ((data["is_multi"] and all(v in data["choices"] for v in data["value"].split()))
                        or not data["is_multi"] and data["value"] in data["choices"]):
                    continue
                if data["is_multi"]:
                    val = " ".join([v for v in data["value"].split() if v in data["choices"]])
                else:
                    val = ""
                val = self._default_options[command][option] if not val else val
                logger.debug("Updating invalid value to default: (command: '%s', option: '%s', "
                             "original value: '%s', new value: '%s')", command, option,
                             self._options[command][option], val)
                self._options[command][option] = val