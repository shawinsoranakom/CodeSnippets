def mimetype(self):
        if self._mimetype == "":
            return _guess_stylesheet_mimetype(self.url)[0]
        return self._mimetype