def setUpClass(cls):
        super().setUpClass()
        params = {
            "DIRS": [],
            "APP_DIRS": True,
            "NAME": cls.backend_name,
            "OPTIONS": cls.options,
        }
        cls.engine = cls.engine_class(params)