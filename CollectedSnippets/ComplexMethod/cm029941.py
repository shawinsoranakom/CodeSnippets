def convert_class(cls):
        nonlocal use_args
        cls_name = cls.__name__
        if use_args is None:
            use_args = etype._use_args_
        __new__ = cls.__dict__.get('__new__')
        if __new__ is not None:
            new_member = __new__.__func__
        else:
            new_member = etype._member_type_.__new__
        attrs = {}
        body = {}
        if __new__ is not None:
            body['__new_member__'] = new_member
        body['_new_member_'] = new_member
        body['_use_args_'] = use_args
        body['_generate_next_value_'] = gnv = etype._generate_next_value_
        body['_member_names_'] = member_names = []
        body['_member_map_'] = member_map = {}
        body['_value2member_map_'] = value2member_map = {}
        body['_hashable_values_'] = hashable_values = []
        body['_unhashable_values_'] = unhashable_values = []
        body['_unhashable_values_map_'] = {}
        body['_member_type_'] = member_type = etype._member_type_
        body['_value_repr_'] = etype._value_repr_
        if issubclass(etype, Flag):
            body['_boundary_'] = boundary or etype._boundary_
            body['_flag_mask_'] = None
            body['_all_bits_'] = None
            body['_singles_mask_'] = None
            body['_inverted_'] = None
            body['__or__'] = Flag.__or__
            body['__xor__'] = Flag.__xor__
            body['__and__'] = Flag.__and__
            body['__ror__'] = Flag.__ror__
            body['__rxor__'] = Flag.__rxor__
            body['__rand__'] = Flag.__rand__
            body['__invert__'] = Flag.__invert__
        for name, obj in cls.__dict__.items():
            if name in ('__dict__', '__weakref__'):
                continue
            if _is_dunder(name) or _is_private(cls_name, name) or _is_sunder(name) or _is_descriptor(obj):
                body[name] = obj
            else:
                attrs[name] = obj
        if cls.__dict__.get('__doc__') is None:
            body['__doc__'] = 'An enumeration.'
        #
        # double check that repr and friends are not the mixin's or various
        # things break (such as pickle)
        # however, if the method is defined in the Enum itself, don't replace
        # it
        enum_class = type(cls_name, (etype, ), body, boundary=boundary, _simple=True)
        for name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            if name not in body:
                # check for mixin overrides before replacing
                enum_method = getattr(etype, name)
                found_method = getattr(enum_class, name)
                object_method = getattr(object, name)
                data_type_method = getattr(member_type, name)
                if found_method in (data_type_method, object_method):
                    setattr(enum_class, name, enum_method)
        gnv_last_values = []
        if issubclass(enum_class, Flag):
            # Flag / IntFlag
            single_bits = multi_bits = 0
            for name, value in attrs.items():
                if isinstance(value, auto) and auto.value is _auto_null:
                    value = gnv(name, 1, len(member_names), gnv_last_values)
                # create basic member (possibly isolate value for alias check)
                if use_args:
                    if not isinstance(value, tuple):
                        value = (value, )
                    member = new_member(enum_class, *value)
                    value = value[0]
                else:
                    member = new_member(enum_class)
                if __new__ is None:
                    member._value_ = value
                # now check if alias
                try:
                    contained = value2member_map.get(member._value_)
                except TypeError:
                    contained = None
                    if member._value_ in unhashable_values or member.value in hashable_values:
                        for m in enum_class:
                            if m._value_ == member._value_:
                                contained = m
                                break
                if contained is not None:
                    # an alias to an existing member
                    contained._add_alias_(name)
                else:
                    # finish creating member
                    member._name_ = name
                    member.__objclass__ = enum_class
                    member.__init__(value)
                    member._sort_order_ = len(member_names)
                    if name not in ('name', 'value'):
                        setattr(enum_class, name, member)
                        member_map[name] = member
                    else:
                        enum_class._add_member_(name, member)
                    value2member_map[value] = member
                    hashable_values.append(value)
                    if _is_single_bit(value):
                        # not a multi-bit alias, record in _member_names_ and _flag_mask_
                        member_names.append(name)
                        single_bits |= value
                    else:
                        multi_bits |= value
                    gnv_last_values.append(value)
            enum_class._flag_mask_ = single_bits | multi_bits
            enum_class._singles_mask_ = single_bits
            enum_class._all_bits_ = 2 ** ((single_bits|multi_bits).bit_length()) - 1
            # set correct __iter__
            member_list = [m._value_ for m in enum_class]
            if member_list != sorted(member_list):
                enum_class._iter_member_ = enum_class._iter_member_by_def_
        else:
            # Enum / IntEnum / StrEnum
            for name, value in attrs.items():
                if isinstance(value, auto):
                    if value.value is _auto_null:
                        value.value = gnv(name, 1, len(member_names), gnv_last_values)
                    value = value.value
                # create basic member (possibly isolate value for alias check)
                if use_args:
                    if not isinstance(value, tuple):
                        value = (value, )
                    member = new_member(enum_class, *value)
                    value = value[0]
                else:
                    member = new_member(enum_class)
                if __new__ is None:
                    member._value_ = value
                # now check if alias
                try:
                    contained = value2member_map.get(member._value_)
                except TypeError:
                    contained = None
                    if member._value_ in unhashable_values or member._value_ in hashable_values:
                        for m in enum_class:
                            if m._value_ == member._value_:
                                contained = m
                                break
                if contained is not None:
                    # an alias to an existing member
                    contained._add_alias_(name)
                else:
                    # finish creating member
                    member._name_ = name
                    member.__objclass__ = enum_class
                    member.__init__(value)
                    member._sort_order_ = len(member_names)
                    if name not in ('name', 'value'):
                        setattr(enum_class, name, member)
                        member_map[name] = member
                    else:
                        enum_class._add_member_(name, member)
                    member_names.append(name)
                    gnv_last_values.append(value)
                    try:
                        # This may fail if value is not hashable. We can't add the value
                        # to the map, and by-value lookups for this value will be
                        # linear.
                        enum_class._value2member_map_.setdefault(value, member)
                        if value not in hashable_values:
                            hashable_values.append(value)
                    except TypeError:
                        # keep track of the value in a list so containment checks are quick
                        enum_class._unhashable_values_.append(value)
                        enum_class._unhashable_values_map_.setdefault(name, []).append(value)
        if '__new__' in body:
            enum_class.__new_member__ = enum_class.__new__
        enum_class.__new__ = Enum.__new__
        return enum_class