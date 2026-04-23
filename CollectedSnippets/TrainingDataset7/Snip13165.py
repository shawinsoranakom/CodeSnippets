def __repr__(self):
        return '<%s template_string="%s...">' % (
            self.__class__.__qualname__,
            self.source[:20].replace("\n", ""),
        )