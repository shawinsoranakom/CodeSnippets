def is_url(self, template):
        """Return True if the name looks like a URL."""
        if ":" not in template:
            return False
        scheme = template.split(":", 1)[0].lower()
        return scheme in self.url_schemes