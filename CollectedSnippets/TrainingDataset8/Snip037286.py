def __init__(
        self,
        key: str,
        description: Optional[str] = None,
        default_val: Optional[Any] = None,
        visibility: str = "visible",
        scriptable: bool = False,
        deprecated: bool = False,
        deprecation_text: Optional[str] = None,
        expiration_date: Optional[str] = None,
        replaced_by: Optional[str] = None,
        type_: type = str,
    ):
        """Create a ConfigOption with the given name.

        Parameters
        ----------
        key : str
            Should be of the form "section.optionName"
            Examples: server.name, deprecation.v1_0_featureName
        description : str
            Like a comment for the config option.
        default_val : any
            The value for this config option.
        visibility : {"visible", "hidden"}
            Whether this option should be shown to users.
        scriptable : bool
            Whether this config option can be set within a user script.
        deprecated: bool
            Whether this config option is deprecated.
        deprecation_text : str or None
            Required if deprecated == True. Set this to a string explaining
            what to use instead.
        expiration_date : str or None
            Required if deprecated == True. set this to the date at which it
            will no longer be accepted. Format: 'YYYY-MM-DD'.
        replaced_by : str or None
            If this is option has been deprecated in favor or another option,
            set this to the path to the new option. Example:
            'server.runOnSave'. If this is set, the 'deprecated' option
            will automatically be set to True, and deprecation_text will have a
            meaningful default (unless you override it).
        type_ : one of str, int, float or bool
            Useful to cast the config params sent by cmd option parameter.
        """
        # Parse out the section and name.
        self.key = key
        key_format = (
            # Capture a group called "section"
            r"(?P<section>"
            # Matching text comprised of letters and numbers that begins
            # with a lowercase letter with an optional "_" preceding it.
            # Examples: "_section", "section1"
            r"\_?[a-z][a-zA-Z0-9]*"
            r")"
            # Separator between groups
            r"\."
            # Capture a group called "name"
            r"(?P<name>"
            # Match text comprised of letters and numbers beginning with a
            # lowercase letter.
            # Examples: "name", "nameOfConfig", "config1"
            r"[a-z][a-zA-Z0-9]*"
            r")$"
        )
        match = re.match(key_format, self.key)
        assert match, f'Key "{self.key}" has invalid format.'
        self.section, self.name = match.group("section"), match.group("name")

        self.description = description

        self.visibility = visibility
        self.scriptable = scriptable
        self.default_val = default_val
        self.deprecated = deprecated
        self.replaced_by = replaced_by
        self.is_default = True
        self._get_val_func: Optional[Callable[[], Any]] = None
        self.where_defined = ConfigOption.DEFAULT_DEFINITION
        self.type = type_

        if self.replaced_by:
            self.deprecated = True
            if deprecation_text is None:
                deprecation_text = "Replaced by %s." % self.replaced_by

        if self.deprecated:
            assert expiration_date, "expiration_date is required for deprecated items"
            assert deprecation_text, "deprecation_text is required for deprecated items"
            self.expiration_date = expiration_date
            self.deprecation_text = textwrap.dedent(deprecation_text)

        self.set_value(default_val)