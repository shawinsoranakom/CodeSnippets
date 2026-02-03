def __eq__(self, other: object) -> bool:

    if not isinstance(other, Deque):
        return NotImplemented

    me = self._front
    oth = other._front

    if len(self) != len(other):
        return False

    while me is not None and oth is not None:
        if me.val != oth.val:
            return False
        me = me.next_node
        oth = oth.next_node

    return True
