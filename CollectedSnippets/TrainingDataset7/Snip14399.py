def __str__(self):
        attrs = {
            "href": iri_to_uri(self._url),
            "type": self.mimetype,
            "media": self.media,
        }
        return flatatt(attrs).strip()