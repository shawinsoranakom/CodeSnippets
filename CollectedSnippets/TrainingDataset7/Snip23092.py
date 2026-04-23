def setUpClass(cls):
        cls.enterClassContext(translation.override("de"))
        super().setUpClass()