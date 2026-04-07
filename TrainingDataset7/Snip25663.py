def __init__(self):
        logging.Handler.__init__(self)
        self.config = settings.LOGGING