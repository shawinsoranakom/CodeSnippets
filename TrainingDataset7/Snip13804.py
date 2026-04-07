def setUpClass(cls):
        cls.selenium = cls.create_webdriver()
        cls.selenium.implicitly_wait(cls.implicit_wait)
        super().setUpClass()
        cls.addClassCleanup(cls._quit_selenium)