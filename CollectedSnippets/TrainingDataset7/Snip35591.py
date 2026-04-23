def setUp(self):
        self.atomic = transaction.atomic()
        self.atomic.__enter__()