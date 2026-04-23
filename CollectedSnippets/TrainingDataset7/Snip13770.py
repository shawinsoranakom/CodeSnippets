def shuffle(self, items, key):
        """
        Return a new list of the items in a shuffled order.

        The `key` is a function that accepts an item in `items` and returns
        a string unique for that item that can be viewed as a string id. The
        order of the return value is deterministic. It depends on the seed
        and key function but not on the original order.
        """
        hashes = {}
        for item in items:
            hashed = self._hash_item(item, key)
            if hashed in hashes:
                msg = "item {!r} has same hash {!r} as item {!r}".format(
                    item,
                    hashed,
                    hashes[hashed],
                )
                raise RuntimeError(msg)
            hashes[hashed] = item
        return [hashes[hashed] for hashed in sorted(hashes)]