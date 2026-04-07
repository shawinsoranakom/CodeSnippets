def __init__(self, stream, descriptions, verbosity):
        self.logger = logging.getLogger("django.db.backends")
        self.logger.setLevel(logging.DEBUG)
        self.handler = None
        super().__init__(stream, descriptions, verbosity)