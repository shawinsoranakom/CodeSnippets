def setUp(self):
        super().setUp()
        activate("de")
        self.addCleanup(deactivate)