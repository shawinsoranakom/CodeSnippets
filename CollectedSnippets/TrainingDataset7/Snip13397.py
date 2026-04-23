def __repr__(self):
        return "<%s view_name='%s' args=%s kwargs=%s as=%s>" % (
            self.__class__.__qualname__,
            self.view_name,
            repr(self.args),
            repr(self.kwargs),
            repr(self.asvar),
        )