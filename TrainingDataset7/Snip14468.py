def __repr__(self):
        if self._wrapped is empty:
            # Avoid recursion if setupfunc is a bound method of this instance.
            if getattr(self._setupfunc, "__self__", None) is self:
                repr_attr = f"<bound method {self._setupfunc.__name__}>"
            else:
                repr_attr = self._setupfunc
        else:
            repr_attr = self._wrapped
        return "<%s: %r>" % (type(self).__name__, repr_attr)