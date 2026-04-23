def attach_alternative(self, content, mimetype):
        """Attach an alternative content representation."""
        if content is None or mimetype is None:
            raise ValueError("Both content and mimetype must be provided.")
        self.alternatives.append(EmailAlternative(content, mimetype))