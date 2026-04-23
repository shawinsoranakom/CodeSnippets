def __new__(metacls, cls, bases, classdict, *, boundary=None, _simple=False, **kwds):
        # an Enum class is final once enumeration items have been defined; it
        # cannot be mixed with other types (int, float, etc.) if it has an
        # inherited __new__ unless a new __new__ is defined (or the resulting
        # class will fail).
        #
        if _simple:
            return super().__new__(metacls, cls, bases, classdict, **kwds)
        #
        # remove any keys listed in _ignore_
        classdict.setdefault('_ignore_', []).append('_ignore_')
        ignore = classdict['_ignore_']
        for key in ignore:
            classdict.pop(key, None)
        #
        # grab member names
        member_names = classdict._member_names
        #
        # check for illegal enum names (any others?)
        invalid_names = set(member_names) & {'mro', ''}
        if invalid_names:
            raise ValueError('invalid enum member name(s) %s'  % (
                    ','.join(repr(n) for n in invalid_names)
                    ))
        #
        # adjust the sunders
        _order_ = classdict.pop('_order_', None)
        _gnv = classdict.get('_generate_next_value_')
        if _gnv is not None and type(_gnv) is not staticmethod:
            _gnv = staticmethod(_gnv)
        # convert to normal dict
        classdict = dict(classdict.items())
        if _gnv is not None:
            classdict['_generate_next_value_'] = _gnv
        #
        # data type of member and the controlling Enum class
        member_type, first_enum = metacls._get_mixins_(cls, bases)
        __new__, save_new, use_args = metacls._find_new_(
                classdict, member_type, first_enum,
                )
        classdict['_new_member_'] = __new__
        classdict['_use_args_'] = use_args
        #
        # convert future enum members into temporary _proto_members
        for name in member_names:
            value = classdict[name]
            classdict[name] = _proto_member(value)
        #
        # house-keeping structures
        classdict['_member_names_'] = []
        classdict['_member_map_'] = {}
        classdict['_value2member_map_'] = {}
        classdict['_hashable_values_'] = []          # for comparing with non-hashable types
        classdict['_unhashable_values_'] = []       # e.g. frozenset() with set()
        classdict['_unhashable_values_map_'] = {}
        classdict['_member_type_'] = member_type
        # now set the __repr__ for the value
        classdict['_value_repr_'] = metacls._find_data_repr_(cls, bases)
        #
        # Flag structures (will be removed if final class is not a Flag)
        classdict['_boundary_'] = (
                boundary
                or getattr(first_enum, '_boundary_', None)
                )
        classdict['_flag_mask_'] = 0
        classdict['_singles_mask_'] = 0
        classdict['_all_bits_'] = 0
        classdict['_inverted_'] = None
        # check for negative flag values and invert if found (using _proto_members)
        if Flag is not None and bases and issubclass(bases[-1], Flag):
            bits = 0
            inverted = []
            for n in member_names:
                p = classdict[n]
                if isinstance(p.value, int):
                    if p.value < 0:
                        inverted.append(p)
                    else:
                        bits |= p.value
                elif p.value is None:
                    pass
                elif isinstance(p.value, tuple) and p.value and isinstance(p.value[0], int):
                    if p.value[0] < 0:
                        inverted.append(p)
                    else:
                        bits |= p.value[0]
            for p in inverted:
                if isinstance(p.value, int):
                    p.value = bits & p.value
                else:
                    p.value = (bits & p.value[0], ) + p.value[1:]
        try:
            classdict['_%s__in_progress' % cls] = True
            enum_class = super().__new__(metacls, cls, bases, classdict, **kwds)
            classdict['_%s__in_progress' % cls] = False
            delattr(enum_class, '_%s__in_progress' % cls)
        except Exception as e:
            # since 3.12 the note "Error calling __set_name__ on '_proto_member' instance ..."
            # is tacked on to the error instead of raising a RuntimeError, so discard it
            if hasattr(e, '__notes__'):
                del e.__notes__
            raise
        # update classdict with any changes made by __init_subclass__
        classdict.update(enum_class.__dict__)
        #
        # double check that repr and friends are not the mixin's or various
        # things break (such as pickle)
        # however, if the method is defined in the Enum itself, don't replace
        # it
        #
        # Also, special handling for ReprEnum
        if ReprEnum is not None and ReprEnum in bases:
            if member_type is object:
                raise TypeError(
                        'ReprEnum subclasses must be mixed with a data type (i.e.'
                        ' int, str, float, etc.)'
                        )
            if '__format__' not in classdict:
                enum_class.__format__ = member_type.__format__
                classdict['__format__'] = enum_class.__format__
            if '__str__' not in classdict:
                method = member_type.__str__
                if method is object.__str__:
                    # if member_type does not define __str__, object.__str__ will use
                    # its __repr__ instead, so we'll also use its __repr__
                    method = member_type.__repr__
                enum_class.__str__ = method
                classdict['__str__'] = enum_class.__str__
        for name in ('__repr__', '__str__', '__format__', '__reduce_ex__'):
            if name not in classdict:
                # check for mixin overrides before replacing
                enum_method = getattr(first_enum, name)
                found_method = getattr(enum_class, name)
                object_method = getattr(object, name)
                data_type_method = getattr(member_type, name)
                if found_method in (data_type_method, object_method):
                    setattr(enum_class, name, enum_method)
        #
        # for Flag, add __or__, __and__, __xor__, and __invert__
        if Flag is not None and issubclass(enum_class, Flag):
            for name in (
                    '__or__', '__and__', '__xor__',
                    '__ror__', '__rand__', '__rxor__',
                    '__invert__'
                ):
                if name not in classdict:
                    enum_method = getattr(Flag, name)
                    setattr(enum_class, name, enum_method)
                    classdict[name] = enum_method
        #
        # replace any other __new__ with our own (as long as Enum is not None,
        # anyway) -- again, this is to support pickle
        if Enum is not None:
            # if the user defined their own __new__, save it before it gets
            # clobbered in case they subclass later
            if save_new:
                enum_class.__new_member__ = __new__
            enum_class.__new__ = Enum.__new__
        #
        # py3 support for definition order (helps keep py2/py3 code in sync)
        #
        # _order_ checking is spread out into three/four steps
        # - if enum_class is a Flag:
        #   - remove any non-single-bit flags from _order_
        # - remove any aliases from _order_
        # - check that _order_ and _member_names_ match
        #
        # step 1: ensure we have a list
        if _order_ is not None:
            if isinstance(_order_, str):
                _order_ = _order_.replace(',', ' ').split()
        #
        # remove Flag structures if final class is not a Flag
        if (
                Flag is None and cls != 'Flag'
                or Flag is not None and not issubclass(enum_class, Flag)
            ):
            delattr(enum_class, '_boundary_')
            delattr(enum_class, '_flag_mask_')
            delattr(enum_class, '_singles_mask_')
            delattr(enum_class, '_all_bits_')
            delattr(enum_class, '_inverted_')
        elif Flag is not None and issubclass(enum_class, Flag):
            # set correct __iter__
            member_list = [m._value_ for m in enum_class]
            if member_list != sorted(member_list):
                enum_class._iter_member_ = enum_class._iter_member_by_def_
            if _order_:
                # _order_ step 2: remove any items from _order_ that are not single-bit
                _order_ = [
                        o
                        for o in _order_
                        if o not in enum_class._member_map_ or _is_single_bit(enum_class[o]._value_)
                        ]
        #
        if _order_:
            # _order_ step 3: remove aliases from _order_
            _order_ = [
                    o
                    for o in _order_
                    if (
                        o not in enum_class._member_map_
                        or
                        (o in enum_class._member_map_ and o in enum_class._member_names_)
                        )]
            # _order_ step 4: verify that _order_ and _member_names_ match
            if _order_ != enum_class._member_names_:
                raise TypeError(
                        'member order does not match _order_:\n  %r\n  %r'
                        % (enum_class._member_names_, _order_)
                        )
        #
        return enum_class