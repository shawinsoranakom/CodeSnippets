def __radd__(self, other):
        "add to another list-like object"
        return other.__class__([*other, *self])