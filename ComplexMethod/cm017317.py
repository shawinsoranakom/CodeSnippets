def __repr__(self):
        return "<%s:%s%s%s%s%s%s%s>" % (
            self.__class__.__qualname__,
            "" if not self.fields else " fields=%s" % repr(self.fields),
            "" if not self.expressions else " expressions=%s" % repr(self.expressions),
            "" if not self.name else " name=%s" % repr(self.name),
            (
                ""
                if self.db_tablespace is None
                else " db_tablespace=%s" % repr(self.db_tablespace)
            ),
            "" if self.condition is None else " condition=%s" % self.condition,
            "" if not self.include else " include=%s" % repr(self.include),
            "" if not self.opclasses else " opclasses=%s" % repr(self.opclasses),
        )