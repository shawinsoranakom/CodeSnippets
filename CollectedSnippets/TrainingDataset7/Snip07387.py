def _rebuild(self, newLen, newItems):
        if newLen and newLen < self._minlength:
            raise ValueError("Must have at least %d items" % self._minlength)
        if self._maxlength is not None and newLen > self._maxlength:
            raise ValueError("Cannot have more than %d items" % self._maxlength)

        self._set_list(newLen, newItems)