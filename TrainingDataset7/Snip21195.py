def test_bare_init(self):
        """Can't replace '__init__' with class name if not in a class."""

        @deprecate_posargs(RemovedAfterNextVersionWarning, ["a"])
        def __init__(*, a):
            pass

        with self.assertDeprecated("'a'", "__init__"):
            __init__(10)