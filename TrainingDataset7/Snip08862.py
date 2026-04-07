def execute(self, *args, **options):
        # sqlmigrate doesn't support coloring its output, so make the
        # BEGIN/COMMIT statements added by output_transaction colorless also.
        self.style.SQL_KEYWORD = lambda noop: noop
        return super().execute(*args, **options)