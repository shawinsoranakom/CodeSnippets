def add_arguments(self, parser):
        try:
            parser.add_argument("--version", action="version", version="A.B.C")
        except ArgumentError:
            pass
        else:
            raise CommandError("--version argument does no yet exist")