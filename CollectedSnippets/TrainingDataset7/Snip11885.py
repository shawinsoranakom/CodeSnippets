def all_parents(self):
        """
        Return all the ancestors of this model as a tuple ordered by MRO.
        Useful for determining if something is an ancestor, regardless of
        lineage.
        """
        result = OrderedSet(self.parents)
        for parent in self.parents:
            for ancestor in parent._meta.all_parents:
                result.add(ancestor)
        return tuple(result)