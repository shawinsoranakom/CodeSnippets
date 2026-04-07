def __init__(self, regex, **kwargs):
        """
        regex can be either a string or a compiled regular expression object.
        """
        kwargs.setdefault("strip", False)
        super().__init__(**kwargs)
        self._set_regex(regex)