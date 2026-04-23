def _validate_value_types(self, *, section="", option="", value=""):
        """Raises a TypeError for illegal non-string values.

        Legal non-string values are UNNAMED_SECTION and falsey values if
        they are allowed.

        For compatibility reasons this method is not used in classic set()
        for RawConfigParsers. It is invoked in every case for mapping protocol
        access and in ConfigParser.set().
        """
        if section is UNNAMED_SECTION:
            if not self._allow_unnamed_section:
                raise UnnamedSectionDisabledError
        elif not isinstance(section, str):
            raise TypeError("section names must be strings or UNNAMED_SECTION")
        if not isinstance(option, str):
            raise TypeError("option keys must be strings")
        if not self._allow_no_value or value:
            if not isinstance(value, str):
                raise TypeError("option values must be strings")