def handle(self, **options):
        if connections[options["database"]].features.supports_inspectdb:
            for line in self.handle_inspection(options):
                self.stdout.write(line)
        else:
            raise CommandError(
                "Database inspection isn't supported for the currently selected "
                "database backend."
            )