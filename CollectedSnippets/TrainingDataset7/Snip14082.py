def match(self, path):
        language_prefix = self.language_prefix
        if path.startswith(language_prefix):
            return path.removeprefix(language_prefix), (), {}
        return None