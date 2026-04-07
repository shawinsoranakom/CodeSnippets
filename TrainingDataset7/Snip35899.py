def handle(self, *app_labels, **options):
        app_labels = set(app_labels)

        if options["empty"]:
            self.stdout.write()
            self.stdout.write("Dave, I can't do that.")
            return

        if not app_labels:
            raise CommandError("I'm sorry Dave, I'm afraid I can't do that.")

        # raise an error if some --parameter is flowing from options to args
        for app_label in app_labels:
            if app_label.startswith("--"):
                raise CommandError("Sorry, Dave, I can't let you do that.")

        self.stdout.write("Dave, my mind is going. I can feel it. I can feel it.")