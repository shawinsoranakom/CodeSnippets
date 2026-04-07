def handle(self, *labels, **options):
        print(
            "EXECUTE:BaseCommand labels=%s, options=%s"
            % (labels, sorted(options.items()))
        )