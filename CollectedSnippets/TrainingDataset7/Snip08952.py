def get_serializer_formats():
    if not _serializers:
        _load_serializers()
    return list(_serializers)