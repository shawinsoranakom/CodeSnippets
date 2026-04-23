def handle_label(self, label, **options):
        print(
            "EXECUTE:LabelCommand label=%s, options=%s"
            % (label, sorted(options.items()))
        )