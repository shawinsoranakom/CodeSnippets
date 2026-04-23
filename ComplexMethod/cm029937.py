def _add_value_alias_(self, value):
        cls = self.__class__
        try:
            if value in cls._value2member_map_:
                if cls._value2member_map_[value] is not self:
                    raise ValueError('%r is already bound: %r' % (value, cls._value2member_map_[value]))
                return
        except TypeError:
            # unhashable value, do long search
            for m in cls._member_map_.values():
                if m._value_ == value:
                    if m is not self:
                        raise ValueError('%r is already bound: %r' % (value, cls._value2member_map_[value]))
                    return
        try:
            # This may fail if value is not hashable. We can't add the value
            # to the map, and by-value lookups for this value will be
            # linear.
            cls._value2member_map_.setdefault(value, self)
            cls._hashable_values_.append(value)
        except TypeError:
            # keep track of the value in a list so containment checks are quick
            cls._unhashable_values_.append(value)
            cls._unhashable_values_map_.setdefault(self.name, []).append(value)