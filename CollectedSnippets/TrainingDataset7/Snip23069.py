def setUpClass(cls):
        cls.enterClassContext(translation.override(None))
        super().setUpClass()