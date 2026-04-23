def setUp(self):
        super().setUp()
        self.smtp_handler.flush_mailbox()
        self.addCleanup(self.smtp_handler.flush_mailbox)