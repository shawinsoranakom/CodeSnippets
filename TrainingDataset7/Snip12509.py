def to_python(self, value):
        """Return a Python boolean object."""
        # Explicitly check for the string 'False', which is what a hidden field
        # will submit for False. Also check for '0', since this is what
        # RadioSelect will provide. Because bool("True") == bool('1') == True,
        # we don't need to handle that explicitly.
        if isinstance(value, str) and value.lower() in ("false", "0"):
            value = False
        else:
            value = bool(value)
        return super().to_python(value)