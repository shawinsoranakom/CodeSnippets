def attr_value(self, target, index=0):
        """
        The attribute value for the given target node (e.g. 'PROJCS'). The
        index keyword specifies an index of the child node to return.
        """
        if not isinstance(target, str) or not isinstance(index, int):
            raise TypeError
        return capi.get_attr_value(self.ptr, force_bytes(target), index)