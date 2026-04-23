def _walk_relationship(self, rel, include_self=False, preserve_ordering=False) -> set[Group] | list[Group]:
        """
        Given `rel` that is an iterable property of Group,
        consitituting a directed acyclic graph among all groups,
        Returns a set of all groups in full tree
        A   B    C
        |  / |  /
        | /  | /
        D -> E
        |  /    vertical connections
        | /     are directed upward
        F
        Called on F, returns set of (A, B, C, D, E)
        """
        seen: set[Group] = set([])
        unprocessed = set(getattr(self, rel))
        if include_self:
            unprocessed.add(self)
        if preserve_ordering:
            ordered: list[Group] = [self] if include_self else []
            ordered.extend(getattr(self, rel))

        while unprocessed:
            seen.update(unprocessed)
            new_unprocessed = set([])

            for new_item in chain.from_iterable(getattr(g, rel) for g in unprocessed):
                new_unprocessed.add(new_item)
                if preserve_ordering:
                    if new_item not in seen:
                        ordered.append(new_item)

            new_unprocessed.difference_update(seen)
            unprocessed = new_unprocessed

        if preserve_ordering:
            return ordered
        return seen