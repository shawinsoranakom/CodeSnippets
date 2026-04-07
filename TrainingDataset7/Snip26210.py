def tearDown(self):
        super().tearDown()
        mail.outbox = []