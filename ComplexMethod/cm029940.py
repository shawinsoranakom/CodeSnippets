def _missing_(cls, value):
        """
        Create a composite member containing all canonical members present in `value`.

        If non-member values are present, result depends on `_boundary_` setting.
        """
        if not isinstance(value, int):
            raise ValueError(
                    "%r is not a valid %s" % (value, cls.__qualname__)
                    )
        # check boundaries
        # - value must be in range (e.g. -16 <-> +15, i.e. ~15 <-> 15)
        # - value must not include any skipped flags (e.g. if bit 2 is not
        #   defined, then 0d10 is invalid)
        flag_mask = cls._flag_mask_
        singles_mask = cls._singles_mask_
        all_bits = cls._all_bits_
        neg_value = None
        if (
                not ~all_bits <= value <= all_bits
                or value & (all_bits ^ flag_mask)
            ):
            if cls._boundary_ is STRICT:
                max_bits = max(value.bit_length(), flag_mask.bit_length())
                raise ValueError(
                        "%r invalid value %r\n    given %s\n  allowed %s" % (
                            cls, value, bin(value, max_bits), bin(flag_mask, max_bits),
                            ))
            elif cls._boundary_ is CONFORM:
                value = value & flag_mask
            elif cls._boundary_ is EJECT:
                return value
            elif cls._boundary_ is KEEP:
                if value < 0:
                    value = (
                            max(all_bits+1, 2**(value.bit_length()))
                            + value
                            )
            else:
                raise ValueError(
                        '%r unknown flag boundary %r' % (cls, cls._boundary_, )
                        )
        if value < 0:
            neg_value = value
            if cls._boundary_ in (EJECT, KEEP):
                value = all_bits + 1 + value
            else:
                value = singles_mask & value
        # get members and unknown
        unknown = value & ~flag_mask
        aliases = value & ~singles_mask
        member_value = value & singles_mask
        if unknown and cls._boundary_ is not KEEP:
            raise ValueError(
                    '%s(%r) -->  unknown values %r [%s]'
                    % (cls.__name__, value, unknown, bin(unknown))
                    )
        # normal Flag?
        if cls._member_type_ is object:
            # construct a singleton enum pseudo-member
            pseudo_member = object.__new__(cls)
        else:
            pseudo_member = cls._member_type_.__new__(cls, value)
        if not hasattr(pseudo_member, '_value_'):
            pseudo_member._value_ = value
        if member_value or aliases:
            members = []
            combined_value = 0
            for m in cls._iter_member_(member_value):
                members.append(m)
                combined_value |= m._value_
            if aliases:
                value = member_value | aliases
                for n, pm in cls._member_map_.items():
                    if pm not in members and pm._value_ and pm._value_ & value == pm._value_:
                        members.append(pm)
                        combined_value |= pm._value_
            unknown = value ^ combined_value
            pseudo_member._name_ = '|'.join([m._name_ for m in members])
            if not combined_value:
                pseudo_member._name_ = None
            elif unknown and cls._boundary_ is STRICT:
                raise ValueError('%r: no members with value %r' % (cls, unknown))
            elif unknown:
                pseudo_member._name_ += '|%s' % cls._numeric_repr_(unknown)
        else:
            pseudo_member._name_ = None
        # use setdefault in case another thread already created a composite
        # with this value
        # note: zero is a special case -- always add it
        pseudo_member = cls._value2member_map_.setdefault(value, pseudo_member)
        if neg_value is not None:
            cls._value2member_map_[neg_value] = pseudo_member
        return pseudo_member