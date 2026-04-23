def handle(self, **options):
        app_name = options.pop("name")
        target = options.pop("directory")
        super().handle("app", app_name, target, **options)