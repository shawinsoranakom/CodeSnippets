def url(self, name):
        """
        Return an absolute URL where the file's contents can be accessed
        directly by a web browser.
        """
        raise NotImplementedError("subclasses of Storage must provide a url() method")