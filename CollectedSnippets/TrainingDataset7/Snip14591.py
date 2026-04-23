def __add__(self, rhs):
        """
        Concatenating a safe string with another safe bytestring or
        safe string is safe. Otherwise, the result is no longer safe.
        """
        if isinstance(rhs, str):
            t = super().__add__(rhs)
            if isinstance(rhs, SafeData):
                t = SafeString(t)
            return t

        # Give the rhs object a chance to handle the addition, for example if
        # the rhs object's class implements `__radd__`. More details:
        # https://docs.python.org/3/reference/datamodel.html#object.__radd__
        return NotImplemented