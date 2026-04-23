def __new__(cls, value):
        # all enum instances are actually created during class construction
        # without calling this method; this method is called by the metaclass'
        # __call__ (i.e. Color(3) ), and by pickle
        if type(value) is cls:
            # For lookups like Color(Color.RED)
            return value
        # by-value search for a matching enum member
        # see if it's in the reverse mapping (for hashable values)
        try:
            return cls._value2member_map_[value]
        except KeyError:
            # Not found, no need to do long O(n) search
            pass
        except TypeError:
            # not there, now do long search -- O(n) behavior
            for name, unhashable_values in cls._unhashable_values_map_.items():
                if value in unhashable_values:
                    return cls[name]
            for name, member in cls._member_map_.items():
                if value == member._value_:
                    return cls[name]
        # still not found -- verify that members exist, in-case somebody got here mistakenly
        # (such as via super when trying to override __new__)
        if not cls._member_map_:
            if getattr(cls, '_%s__in_progress' % cls.__name__, False):
                raise TypeError('do not use `super().__new__; call the appropriate __new__ directly') from None
            raise TypeError("%r has no members defined" % cls)
        #
        # still not found -- try _missing_ hook
        try:
            exc = None
            result = cls._missing_(value)
        except Exception as e:
            exc = e
            result = None
        try:
            if isinstance(result, cls):
                return result
            elif (
                    Flag is not None and issubclass(cls, Flag)
                    and cls._boundary_ is EJECT and isinstance(result, int)
                ):
                return result
            else:
                ve_exc = ValueError("%r is not a valid %s" % (value, cls.__qualname__))
                if result is None and exc is None:
                    raise ve_exc
                elif exc is None:
                    exc = TypeError(
                            'error in %s._missing_: returned %r instead of None or a valid member'
                            % (cls.__name__, result)
                            )
                if not isinstance(exc, ValueError):
                    exc.__context__ = ve_exc
                raise exc
        finally:
            # ensure all variables that could hold an exception are destroyed
            exc = None
            ve_exc = None