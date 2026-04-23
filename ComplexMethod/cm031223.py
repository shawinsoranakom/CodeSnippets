def search(self, pattern, index, stopindex=None,
            forwards=None, backwards=None, exact=None,
            regexp=None, nocase=None, count=None,
            elide=None, *, nolinestop=None, strictlimits=None):
        """Search PATTERN beginning from INDEX until STOPINDEX.
        Return the index of the first character of a match or an
        empty string."""
        args = [self._w, 'search']
        if forwards: args.append('-forwards')
        if backwards: args.append('-backwards')
        if exact: args.append('-exact')
        if regexp: args.append('-regexp')
        if nocase: args.append('-nocase')
        if elide: args.append('-elide')
        if count: args.append('-count'); args.append(count)
        if nolinestop: args.append('-nolinestop')
        if strictlimits: args.append('-strictlimits')
        if pattern and pattern[0] == '-': args.append('--')
        args.append(pattern)
        args.append(index)
        if stopindex is not None: args.append(stopindex)
        return str(self.tk.call(tuple(args)))