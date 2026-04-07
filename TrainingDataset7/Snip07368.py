def __delitem__(self, index):
        "Delete the item(s) at the specified index/slice."
        if not isinstance(index, (int, slice)):
            raise TypeError("%s is not a legal index" % index)

        # calculate new length and dimensions
        origLen = len(self)
        if isinstance(index, int):
            index = self._checkindex(index)
            indexRange = [index]
        else:
            indexRange = range(*index.indices(origLen))

        newLen = origLen - len(indexRange)
        newItems = (
            self._get_single_internal(i) for i in range(origLen) if i not in indexRange
        )

        self._rebuild(newLen, newItems)