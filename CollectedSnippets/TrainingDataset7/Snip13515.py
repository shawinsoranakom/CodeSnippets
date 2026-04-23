def led(self, left, parser):
        # Left denotation - called in infix context
        raise parser.error_class(
            "Not expecting '%s' as infix operator in if tag." % self.id
        )