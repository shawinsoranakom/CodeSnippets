def set_options(self, **options):
        """
        Set instance variables based on an options dict
        """
        self.interactive = options["interactive"]
        self.verbosity = options["verbosity"]
        self.symlink = options["link"]
        self.clear = options["clear"]
        self.dry_run = options["dry_run"]
        ignore_patterns = options["ignore_patterns"]
        if options["use_default_ignore_patterns"]:
            ignore_patterns += apps.get_app_config("staticfiles").ignore_patterns
        self.ignore_patterns = list({os.path.normpath(p) for p in ignore_patterns})
        self.post_process = options["post_process"]