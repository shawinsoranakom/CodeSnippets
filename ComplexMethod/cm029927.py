def __set_name__(self, enum_class, member_name):
        """
        convert each quasi-member into an instance of the new enum class
        """
        # first step: remove ourself from enum_class
        delattr(enum_class, member_name)
        # second step: create member based on enum_class
        value = self.value
        if not isinstance(value, tuple):
            args = (value, )
        else:
            args = value
        if enum_class._member_type_ is tuple:   # special case for tuple enums
            args = (args, )     # wrap it one more time
        if not enum_class._use_args_:
            enum_member = enum_class._new_member_(enum_class)
        else:
            enum_member = enum_class._new_member_(enum_class, *args)
        if not hasattr(enum_member, '_value_'):
            if enum_class._member_type_ is object:
                enum_member._value_ = value
            else:
                try:
                    enum_member._value_ = enum_class._member_type_(*args)
                except Exception as exc:
                    new_exc = TypeError(
                            '_value_ not set in __new__, unable to create it'
                            )
                    new_exc.__cause__ = exc
                    raise new_exc
        value = enum_member._value_
        enum_member._name_ = member_name
        enum_member.__objclass__ = enum_class
        enum_member.__init__(*args)
        enum_member._sort_order_ = len(enum_class._member_names_)

        if Flag is not None and issubclass(enum_class, Flag):
            if isinstance(value, int):
                enum_class._flag_mask_ |= value
                if _is_single_bit(value):
                    enum_class._singles_mask_ |= value
            enum_class._all_bits_ = 2 ** ((enum_class._flag_mask_).bit_length()) - 1

        # If another member with the same value was already defined, the
        # new member becomes an alias to the existing one.
        try:
            try:
                # try to do a fast lookup to avoid the quadratic loop
                enum_member = enum_class._value2member_map_[value]
            except TypeError:
                for name, canonical_member in enum_class._member_map_.items():
                    if canonical_member._value_ == value:
                        enum_member = canonical_member
                        break
                else:
                    raise KeyError
        except KeyError:
            # this could still be an alias if the value is multi-bit and the
            # class is a flag class
            if (
                    Flag is None
                    or not issubclass(enum_class, Flag)
                ):
                # no other instances found, record this member in _member_names_
                enum_class._member_names_.append(member_name)
            elif (
                    Flag is not None
                    and issubclass(enum_class, Flag)
                    and isinstance(value, int)
                    and _is_single_bit(value)
                ):
                # no other instances found, record this member in _member_names_
                enum_class._member_names_.append(member_name)

        enum_class._add_member_(member_name, enum_member)
        try:
            # This may fail if value is not hashable. We can't add the value
            # to the map, and by-value lookups for this value will be
            # linear.
            enum_class._value2member_map_.setdefault(value, enum_member)
            if value not in enum_class._hashable_values_:
                enum_class._hashable_values_.append(value)
        except TypeError:
            # keep track of the value in a list so containment checks are quick
            enum_class._unhashable_values_.append(value)
            enum_class._unhashable_values_map_.setdefault(member_name, []).append(value)