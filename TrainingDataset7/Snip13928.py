def __init__(self, application):
        self.application = application
        self.base_url = urlparse(self.get_base_url())
        super().__init__()