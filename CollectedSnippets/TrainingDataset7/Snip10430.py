def __init__(
        self,
        defaults=None,
        specified_apps=None,
        dry_run=None,
        verbosity=1,
        log=None,
    ):
        self.verbosity = verbosity
        self.log = log
        super().__init__(
            defaults=defaults,
            specified_apps=specified_apps,
            dry_run=dry_run,
        )