def setUp(self):
        self.addCleanup(csp_reports.clear)
        super().setUp()