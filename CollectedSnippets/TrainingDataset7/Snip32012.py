def setUpClass(cls):
        super().setUpClass()
        cls.foo = getattr(settings, "TEST", "BUG")