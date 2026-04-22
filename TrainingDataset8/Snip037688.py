def validate_int_bounds(cls, value: int, value_name: Optional[str] = None) -> None:
        """Validate that an int value can be represented with perfect precision
        by a JavaScript Number.

        Parameters
        ----------
        value : int
        value_name : str or None
            The name of the value parameter. If specified, this will be used
            in any exception that is thrown.

        Raises
        -------
        JSNumberBoundsException
            Raised with a human-readable explanation if the value falls outside
            JavaScript int bounds.

        """
        if value_name is None:
            value_name = "value"

        if value < cls.MIN_SAFE_INTEGER:
            raise JSNumberBoundsException(
                "%s (%s) must be >= -((1 << 53) - 1)" % (value_name, value)
            )
        elif value > cls.MAX_SAFE_INTEGER:
            raise JSNumberBoundsException(
                "%s (%s) must be <= (1 << 53) - 1" % (value_name, value)
            )