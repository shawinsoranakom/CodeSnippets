def runtime_checkable(cls):
    """Mark a protocol class as a runtime protocol.

    Such protocol can be used with isinstance() and issubclass().
    Raise TypeError if applied to a non-protocol class.
    This allows a simple-minded structural check very similar to
    one trick ponies in collections.abc such as Iterable.

    For example::

        @runtime_checkable
        class Closable(Protocol):
            def close(self): ...

        assert isinstance(open('/some/file'), Closable)

    Warning: this will check only the presence of the required methods,
    not their type signatures!
    """
    if not issubclass(cls, Generic) or not getattr(cls, '_is_protocol', False):
        raise TypeError('@runtime_checkable can be only applied to protocol classes,'
                        ' got %r' % cls)
    cls._is_runtime_protocol = True
    # See GH-132604.
    if hasattr(cls, '__typing_is_deprecated_inherited_runtime_protocol__'):
        cls.__typing_is_deprecated_inherited_runtime_protocol__ = False
    # PEP 544 prohibits using issubclass()
    # with protocols that have non-method members.
    # See gh-113320 for why we compute this attribute here,
    # rather than in `_ProtocolMeta.__init__`
    cls.__non_callable_proto_members__ = set()
    for attr in cls.__protocol_attrs__:
        try:
            is_callable = callable(getattr(cls, attr, None))
        except Exception as e:
            raise TypeError(
                f"Failed to determine whether protocol member {attr!r} "
                "is a method member"
            ) from e
        else:
            if not is_callable:
                cls.__non_callable_proto_members__.add(attr)
    return cls