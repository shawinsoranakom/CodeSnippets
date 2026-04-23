def __subclasscheck__(cls, other):
        if cls is Protocol:
            return type.__subclasscheck__(cls, other)
        if (
            getattr(cls, '_is_protocol', False)
            and not _allow_reckless_class_checks()
        ):
            if not getattr(cls, '_is_runtime_protocol', False):
                _type_check_issubclass_arg_1(other)
                raise TypeError(
                    "Instance and class checks can only be used with "
                    "@runtime_checkable protocols"
                )
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
            if (
                # this attribute is set by @runtime_checkable:
                cls.__non_callable_proto_members__
                and cls.__dict__.get("__subclasshook__") is _proto_hook
            ):
                _type_check_issubclass_arg_1(other)
                non_method_attrs = sorted(cls.__non_callable_proto_members__)
                raise TypeError(
                    "Protocols with non-method members don't support issubclass()."
                    f" Non-method members: {str(non_method_attrs)[1:-1]}."
                )
        return _abc_subclasscheck(cls, other)