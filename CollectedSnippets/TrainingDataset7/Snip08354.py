def __repr__(self):
        return "<%s: level=%r, msg=%r, hint=%r, obj=%r, id=%r>" % (
            self.__class__.__name__,
            self.level,
            self.msg,
            self.hint,
            self.obj,
            self.id,
        )