def save_file(self, name):
        name = self.storage.save(name, SlowFile(b"Data"))