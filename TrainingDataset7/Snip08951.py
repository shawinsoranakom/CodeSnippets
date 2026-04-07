def get_serializer(format):
    if not _serializers:
        _load_serializers()
    if format not in _serializers:
        raise SerializerDoesNotExist(format)
    return _serializers[format].Serializer