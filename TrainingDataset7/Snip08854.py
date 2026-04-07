def handle(self, *args, **options):
        self.verbosity = options["verbosity"]

        # Get the database we're operating from
        db = options["database"]
        connection = connections[db]

        if options["format"] == "plan":
            return self.show_plan(connection, options["app_label"])
        else:
            return self.show_list(connection, options["app_label"])