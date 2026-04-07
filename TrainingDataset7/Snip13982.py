def keys(self):
        """
        Flattened keys of subcontexts.
        """
        return set(chain.from_iterable(d for subcontext in self for d in subcontext))