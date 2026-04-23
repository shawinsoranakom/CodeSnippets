def _match_normalized_structure(a, b):
        if a is b:
            return True
        if _normalize_type(a.type) != _normalize_type(b.type):
            return False
        if a.type is dict and b.type is dict:
            # in the case of dict, the context is list of keys and we allow the keys to be in any order
            if set(a.context) != set(b.context):
                return False
        elif a.context != b.context:
            return False
        if a.num_children != b.num_children:
            return False
        return all(
            _match_normalized_structure(a, b)
            for a, b in zip(a.children(), b.children())
        )