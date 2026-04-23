def setUpClass(cls):
        cls.engine = Engine(
            dirs=[TEMPLATE_DIR], loaders=["django.template.loaders.filesystem.Loader"]
        )
        super().setUpClass()