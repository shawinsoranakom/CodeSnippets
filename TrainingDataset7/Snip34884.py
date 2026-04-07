def __init__(
        self,
        verbosity=1,
        interactive=True,
        failfast=True,
        option_a=None,
        option_b=None,
        option_c=None,
        **kwargs,
    ):
        super().__init__(
            verbosity=verbosity, interactive=interactive, failfast=failfast
        )
        self.option_a = option_a
        self.option_b = option_b
        self.option_c = option_c