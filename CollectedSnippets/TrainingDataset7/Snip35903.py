def handle(self, *args, **options):
        for option, value in options.items():
            if value is not None:
                self.stdout.write("%s=%s" % (option, value))