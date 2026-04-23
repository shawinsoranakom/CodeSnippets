def _get_single_internal(self, index):
        """
        Return the ring at the specified index. The first index, 0, will
        always return the exterior ring. Indices > 0 will return the
        interior ring at the given index (e.g., poly[1] and poly[2] would
        return the first and second interior ring, respectively).

        CAREFUL: Internal/External are not the same as Interior/Exterior!
        Return a pointer from the existing geometries for use internally by the
        object's methods. _get_single_external() returns a clone of the same
        geometry for use by external code.
        """
        if index == 0:
            return capi.get_extring(self.ptr)
        else:
            # Getting the interior ring, have to subtract 1 from the index.
            return capi.get_intring(self.ptr, index - 1)