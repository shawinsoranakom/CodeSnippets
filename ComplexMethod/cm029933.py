def _find_data_type_(mcls, class_name, bases):
        # a datatype has a __new__ method, or a __dataclass_fields__ attribute
        data_types = set()
        base_chain = set()
        for chain in bases:
            candidate = None
            for base in chain.__mro__:
                base_chain.add(base)
                if base is object:
                    continue
                elif isinstance(base, EnumType):
                    if base._member_type_ is not object:
                        data_types.add(base._member_type_)
                        break
                elif '__new__' in base.__dict__ or '__dataclass_fields__' in base.__dict__:
                    data_types.add(candidate or base)
                    break
                else:
                    candidate = candidate or base
        if len(data_types) > 1:
            raise TypeError('too many data types for %r: %r' % (class_name, data_types))
        elif data_types:
            return data_types.pop()
        else:
            return None