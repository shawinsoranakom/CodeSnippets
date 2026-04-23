def __instancecheck__(cls, instance):
        # We need this method for situations where attributes are
        # assigned in __init__.
        if cls is Protocol:
            return type.__instancecheck__(cls, instance)
        if not getattr(cls, "_is_protocol", False):
            # i.e., it's a concrete subclass of a protocol
            return _abc_instancecheck(cls, instance)

        if (
            not getattr(cls, '_is_runtime_protocol', False) and
            not _allow_reckless_class_checks()
        ):
            raise TypeError("Instance and class checks can only be used with"
                            " @runtime_checkable protocols")

        if getattr(cls, '__typing_is_deprecated_inherited_runtime_protocol__', False):
            # See GH-132604.
            import warnings

            depr_message = (
                f"{cls!r} isn't explicitly decorated with @runtime_checkable but "
                "it is used in issubclass() or isinstance(). Instance and class "
                "checks can only be used with @runtime_checkable protocols. "
                "This will raise a TypeError in Python 3.20."
            )
            warnings.warn(depr_message, category=DeprecationWarning, stacklevel=2)

        if _abc_instancecheck(cls, instance):
            return True

        getattr_static = _lazy_load_getattr_static()
        for attr in cls.__protocol_attrs__:
            try:
                val = getattr_static(instance, attr)
            except AttributeError:
                break
            # this attribute is set by @runtime_checkable:
            if val is None and attr not in cls.__non_callable_proto_members__:
                break
        else:
            return True

        return False