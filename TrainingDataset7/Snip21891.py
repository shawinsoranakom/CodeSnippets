def _save(self, name, content):
        if content:
            return super()._save(name, content)
        return ""