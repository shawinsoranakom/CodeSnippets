def __init__(
        self, defaults=None, specified_apps=None, dry_run=None, prompt_output=None
    ):
        super().__init__(
            defaults=defaults, specified_apps=specified_apps, dry_run=dry_run
        )
        self.prompt_output = prompt_output or OutputWrapper(sys.stdout)