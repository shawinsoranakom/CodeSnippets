def setUpClass(cls):
        cls.enterClassContext(translation.override("en-us"))
        super().setUpClass()