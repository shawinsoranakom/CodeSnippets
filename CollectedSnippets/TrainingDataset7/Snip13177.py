def __repr__(self):
        token_name = self.token_type.name.capitalize()
        return '<%s token: "%s...">' % (
            token_name,
            self.contents[:20].replace("\n", ""),
        )