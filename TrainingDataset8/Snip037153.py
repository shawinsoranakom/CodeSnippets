def docstrings():
    """Docstring. Should not be printed."""

    def nested():
        """Multiline docstring.
        Should not be printed."""
        pass

    class Foo(object):
        """Class docstring. Should not be printed."""

        pass

    nested()