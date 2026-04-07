def tearDown(self):
        self.logger.handlers[0].stream = self.old_stream