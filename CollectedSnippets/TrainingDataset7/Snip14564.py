def filter(self, record):
        if self.callback(record):
            return 1
        return 0