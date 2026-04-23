def _save(self, name, content):
        """
        This method is important to test that Storage.save() doesn't replace
        '\' with '/' (rather FileSystemStorage.save() does).
        """
        return name