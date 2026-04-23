def _contains_aggregate(cls, obj):
        if isinstance(obj, tree.Node):
            return any(cls._contains_aggregate(c) for c in obj.children)
        return obj.contains_aggregate