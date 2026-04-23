def register_serializer(format, serializer_module, serializers=None):
    """Register a new serializer.

    ``serializer_module`` should be the fully qualified module name
    for the serializer.

    If ``serializers`` is provided, the registration will be added
    to the provided dictionary.

    If ``serializers`` is not provided, the registration will be made
    directly into the global register of serializers. Adding serializers
    directly is not a thread-safe operation.
    """
    if serializers is None and not _serializers:
        _load_serializers()

    try:
        module = importlib.import_module(serializer_module)
    except ImportError as exc:
        bad_serializer = BadSerializer(exc)

        module = type(
            "BadSerializerModule",
            (),
            {
                "Deserializer": bad_serializer,
                "Serializer": bad_serializer,
            },
        )

    if serializers is None:
        _serializers[format] = module
    else:
        serializers[format] = module