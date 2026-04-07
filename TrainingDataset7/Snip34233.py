def setUpClass(cls):
        cls.engine = Engine(app_dirs=True, libraries=LIBRARIES)
        super().setUpClass()