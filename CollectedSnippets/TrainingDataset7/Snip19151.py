def setUp(self):
        # The super calls needs to happen first for the settings override.
        super().setUp()
        self.create_table()
        self.addCleanup(self.drop_table)