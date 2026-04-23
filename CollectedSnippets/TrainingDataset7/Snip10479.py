def serialize(self):
        return "uuid.%s" % repr(self.value), {"import uuid"}