def _validate_selection(self, value: str | list[str]) -> str | list[str]:
        """ Validate that the given value is valid within the stored choices

        Parameters
        ----------
        str | list[str]
            The inbound config value to validate

        Returns
        -------
        bool
            ``True`` if the selected value is a valid choice
        """
        assert isinstance(self.choices, list)
        choices = [x.lower() for x in self.choices]
        logger.debug("[%s] Checking config choices", self._name)

        if isinstance(value, str):
            if value.lower() not in choices:
                logger.warning("[%s] '%s' is not a valid config choice. Defaulting to '%s'",
                               self._name, value, self.default)
                return cast(str, self.default)
            return value

        if all(x.lower() in choices for x in value):
            return value

        valid = [x for x in value if x.lower() in choices]
        valid = valid if valid else cast(list[str], self.default)
        invalid = [x for x in value if x.lower() not in choices]
        logger.warning("[%s] The option(s) %s are not valid selections. Setting to: %s",
                       self._name, invalid, valid)

        return valid