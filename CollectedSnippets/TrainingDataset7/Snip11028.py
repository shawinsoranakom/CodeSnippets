def __deepcopy__(self, memodict):
        # We don't have to deepcopy very much here, since most things are not
        # intended to be altered after initial creation.
        obj = copy.copy(self)
        if self.remote_field:
            obj.remote_field = copy.copy(self.remote_field)
            if hasattr(self.remote_field, "field") and self.remote_field.field is self:
                obj.remote_field.field = obj
        memodict[id(self)] = obj
        return obj