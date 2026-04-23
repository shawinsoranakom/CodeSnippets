def nud(self, parser):
        # Null denotation - called in prefix context
        raise parser.error_class(
            "Not expecting '%s' in this position in if tag." % self.id
        )