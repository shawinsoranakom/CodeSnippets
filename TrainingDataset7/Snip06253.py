def execute(self, *args, **options):
        self.stdin = options.get("stdin", sys.stdin)  # Used for testing
        return super().execute(*args, **options)