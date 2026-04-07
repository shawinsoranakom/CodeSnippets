def __repr__(self):
        return "<%(cls)s [%(methods)s] status_code=%(status_code)d%(content_type)s>" % {
            "cls": self.__class__.__name__,
            "status_code": self.status_code,
            "content_type": self._content_type_for_repr,
            "methods": self["Allow"],
        }