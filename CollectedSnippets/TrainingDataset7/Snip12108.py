def merge_dicts(dicts):
        """
        Merge dicts in reverse to preference the order of the original list.
        e.g., merge_dicts([a, b]) will preference the keys in 'a' over those in
        'b'.
        """
        merged = {}
        for d in reversed(dicts):
            merged.update(d)
        return merged