def setUp(self):
        super().setUp()
        self.client = Client(enforce_csrf_checks=True)