def setUpClass(cls):
        cls.engine = Engine(
            loaders=["django.template.loaders.app_directories.Loader"],
        )
        super().setUpClass()