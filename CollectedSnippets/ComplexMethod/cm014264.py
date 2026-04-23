def __post_init__(self, /) -> None:
        if self._type is None:
            assert len(self._children) == 0
            assert self._metadata is None
            assert self._entries == ()
            assert self._unflatten_func is None
            num_nodes = 1
            num_leaves = 1
            num_children = 0
        else:
            assert callable(self._unflatten_func)
            num_nodes = 1
            num_leaves = 0
            for child in self._children:
                num_nodes += child.num_nodes
                num_leaves += child.num_leaves
            num_children = len(self._children)

        object.__setattr__(self, "num_nodes", num_nodes)
        object.__setattr__(self, "num_leaves", num_leaves)
        object.__setattr__(self, "num_children", num_children)