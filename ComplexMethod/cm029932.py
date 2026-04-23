def _find_data_repr_(mcls, class_name, bases):
        for chain in bases:
            for base in chain.__mro__:
                if base is object:
                    continue
                elif isinstance(base, EnumType):
                    # if we hit an Enum, use it's _value_repr_
                    return base._value_repr_
                elif '__repr__' in base.__dict__:
                    # this is our data repr
                    # double-check if a dataclass with a default __repr__
                    if (
                            '__dataclass_fields__' in base.__dict__
                            and '__dataclass_params__' in base.__dict__
                            and base.__dict__['__dataclass_params__'].repr
                        ):
                        return _dataclass_repr
                    else:
                        return base.__dict__['__repr__']
        return None