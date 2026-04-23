def search_all(self, pattern, index, stopindex=None, *,
            forwards=None, backwards=None, exact=None,
            regexp=None, nocase=None, count=None,
            elide=None, nolinestop=None, overlap=None,
            strictlimits=None):
        """Search all occurrences of PATTERN from INDEX to STOPINDEX.
        Return a tuple of indices where matches begin."""
        args = [self._w, 'search', '-all']
        if forwards: args.append('-forwards')
        if backwards: args.append('-backwards')
        if exact: args.append('-exact')
        if regexp: args.append('-regexp')
        if nocase: args.append('-nocase')
        if elide: args.append('-elide')
        if count: args.append('-count'); args.append(count)
        if nolinestop: args.append('-nolinestop')
        if overlap: args.append('-overlap')
        if strictlimits: args.append('-strictlimits')
        if pattern and pattern[0] == '-': args.append('--')
        args.append(pattern)
        args.append(index)
        if stopindex is not None: args.append(stopindex)
        result = self.tk.call(tuple(args))
        return self.tk.splitlist(result)