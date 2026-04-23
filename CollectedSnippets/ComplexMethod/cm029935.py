def _add_member_(cls, name, member):
        # _value_ structures are not updated
        if name in cls._member_map_:
            if cls._member_map_[name] is not member:
                raise NameError('%r is already bound: %r' % (name, cls._member_map_[name]))
            return
        #
        # if necessary, get redirect in place and then add it to _member_map_
        found_descriptor = None
        descriptor_type = None
        class_type = None
        for base in cls.__mro__[1:]:
            attr = base.__dict__.get(name)
            if attr is not None:
                if isinstance(attr, (property, DynamicClassAttribute)):
                    found_descriptor = attr
                    class_type = base
                    descriptor_type = 'enum'
                    break
                elif _is_descriptor(attr):
                    found_descriptor = attr
                    descriptor_type = descriptor_type or 'desc'
                    class_type = class_type or base
                    continue
                else:
                    descriptor_type = 'attr'
                    class_type = base
        if found_descriptor:
            redirect = property()
            redirect.member = member
            redirect.__set_name__(cls, name)
            if descriptor_type in ('enum', 'desc'):
                # earlier descriptor found; copy fget, fset, fdel to this one.
                redirect.fget = getattr(found_descriptor, 'fget', None)
                redirect._get = getattr(found_descriptor, '__get__', None)
                redirect.fset = getattr(found_descriptor, 'fset', None)
                redirect._set = getattr(found_descriptor, '__set__', None)
                redirect.fdel = getattr(found_descriptor, 'fdel', None)
                redirect._del = getattr(found_descriptor, '__delete__', None)
            redirect._attr_type = descriptor_type
            redirect._cls_type = class_type
            setattr(cls, name, redirect)
        else:
            setattr(cls, name, member)
        # now add to _member_map_ (even aliases)
        cls._member_map_[name] = member