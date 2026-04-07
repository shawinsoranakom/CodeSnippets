def _assign_extended_slice_rebuild(self, start, stop, step, valueList):
        "Assign an extended slice by rebuilding entire list"
        indexList = range(start, stop, step)
        # extended slice, only allow assigning slice of same size
        if len(valueList) != len(indexList):
            raise ValueError(
                "attempt to assign sequence of size %d "
                "to extended slice of size %d" % (len(valueList), len(indexList))
            )

        # we're not changing the length of the sequence
        newLen = len(self)
        newVals = dict(zip(indexList, valueList))

        def newItems():
            for i in range(newLen):
                if i in newVals:
                    yield newVals[i]
                else:
                    yield self._get_single_internal(i)

        self._rebuild(newLen, newItems())