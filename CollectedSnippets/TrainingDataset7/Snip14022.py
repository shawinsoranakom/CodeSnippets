def setUp(self):
        self.logger = logging.getLogger("django")
        self.old_stream = self.logger.handlers[0].stream
        self.logger_output = StringIO()
        self.logger.handlers[0].stream = self.logger_output