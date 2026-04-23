def _response(self, filepath):
        return self.client.get(quote(posixpath.join(settings.STATIC_URL, filepath)))