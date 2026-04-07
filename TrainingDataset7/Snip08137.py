def local(self):
        try:
            self.storage.path("")
        except NotImplementedError:
            return False
        return True