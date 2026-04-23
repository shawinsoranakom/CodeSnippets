def docother(self, object, name=None, mod=None, parent=None, *ignored,
                 maxlen=None, doc=None):
        """Produce text documentation for a data object."""
        repr = self.repr(object)
        if maxlen:
            line = (name and name + ' = ' or '') + repr
            chop = maxlen - len(line)
            if chop < 0: repr = repr[:chop] + '...'
        line = (name and self.bold(name) + ' = ' or '') + repr
        if not doc:
            doc = getdoc(object)
        if doc:
            line += '\n' + self.indent(str(doc)) + '\n'
        return line