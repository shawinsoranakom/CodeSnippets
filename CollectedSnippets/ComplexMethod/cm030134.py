def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)

        # Determine if this is a protocol or a concrete subclass.
        if not cls.__dict__.get('_is_protocol', False):
            cls._is_protocol = any(b is Protocol for b in cls.__bases__)

        # Mark inherited runtime checkability (deprecated). See GH-132604.
        if cls._is_protocol and getattr(cls, '_is_runtime_protocol', False):
            # This flag is set to False by @runtime_checkable.
            cls.__typing_is_deprecated_inherited_runtime_protocol__ = True

        # Set (or override) the protocol subclass hook.
        if '__subclasshook__' not in cls.__dict__:
            cls.__subclasshook__ = _proto_hook

        # Prohibit instantiation for protocol classes
        if cls._is_protocol and cls.__init__ is Protocol.__init__:
            cls.__init__ = _no_init_or_replace_init