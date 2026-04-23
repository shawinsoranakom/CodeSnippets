def from_lookup(cls, lookup):
        transform, *keys = lookup.split(LOOKUP_SEP)
        if not keys:
            raise ValueError("Lookup must contain key or index transforms.")
        for key in keys:
            transform = cls(key, transform)
        return transform