def newItems():
            for i in range(newLen):
                if i in newVals:
                    yield newVals[i]
                else:
                    yield self._get_single_internal(i)