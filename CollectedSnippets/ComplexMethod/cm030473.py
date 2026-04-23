def _fold(self, name, value, refold_binary=False):
        if hasattr(value, 'name'):
            return value.fold(policy=self)
        maxlen = self.max_line_length if self.max_line_length else sys.maxsize
        # We can't use splitlines here because it splits on more than \r and \n.
        lines = linesep_splitter.split(value)
        refold = (self.refold_source == 'all' or
                  self.refold_source == 'long' and
                    (lines and len(lines[0])+len(name)+2 > maxlen or
                     any(len(x) > maxlen for x in lines[1:])))

        if not refold:
            if not self.utf8:
                refold = not value.isascii()
            elif refold_binary:
                refold = _has_surrogates(value)
        if refold:
            return self.header_factory(name, ''.join(lines)).fold(policy=self)

        return name + ': ' + self.linesep.join(lines) + self.linesep