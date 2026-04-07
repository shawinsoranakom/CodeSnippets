def load(self, data):
            return self.orig_loader.load(data).replace(tzinfo=self.timezone)