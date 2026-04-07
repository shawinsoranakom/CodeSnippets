def _set_regex(self, regex):
        if isinstance(regex, str):
            regex = re.compile(regex)
        self._regex = regex
        if (
            hasattr(self, "_regex_validator")
            and self._regex_validator in self.validators
        ):
            self.validators.remove(self._regex_validator)
        self._regex_validator = validators.RegexValidator(regex=regex)
        self.validators.append(self._regex_validator)