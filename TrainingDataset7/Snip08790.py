def read(self):
        return zipfile.ZipFile.read(self, self.namelist()[0])