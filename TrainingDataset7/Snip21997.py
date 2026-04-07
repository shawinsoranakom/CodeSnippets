def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        with open(os.path.join(self.upload_dir, self.file_name), "wb") as fp:
            fp.write(self.file.read())
        return self.file