def handle(self, *args, **options):
        example = options["example"]
        if example == "raise":
            raise CommandError(returncode=3)
        if options["verbosity"] > 0:
            self.stdout.write("I don't feel like dancing %s." % options["style"])
            self.stdout.write(",".join(options))
        if options["integer"] > 0:
            self.stdout.write(
                "You passed %d as a positional argument." % options["integer"]
            )