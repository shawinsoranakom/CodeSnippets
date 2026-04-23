def __repr__(self):
        return "<%s: condition=%s name=%s%s%s>" % (
            self.__class__.__qualname__,
            self.condition,
            repr(self.name),
            (
                ""
                if self.violation_error_code is None
                else " violation_error_code=%r" % self.violation_error_code
            ),
            (
                ""
                if self.violation_error_message is None
                or self.violation_error_message == self.default_violation_error_message
                else " violation_error_message=%r" % self.violation_error_message
            ),
        )