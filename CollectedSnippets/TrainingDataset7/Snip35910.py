def handle(self, *args, **options):
        for option, value in options.items():
            self.stdout.write("%s=%s" % (option, value))