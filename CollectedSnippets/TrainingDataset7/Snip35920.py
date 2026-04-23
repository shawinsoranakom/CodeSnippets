def handle(self, *args, **options):
        self.stdout.write(",".join(options))