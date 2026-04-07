def __deepcopy__(self, memodict):
        """
        The `deepcopy` routine is used by the `Node` class of
        django.utils.tree; thus, the protocol routine needs to be implemented
        to return correct copies (clones) of these GEOS objects, which use C
        pointers.
        """
        return self.clone()