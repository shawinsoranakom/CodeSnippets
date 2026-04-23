def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        return self.file