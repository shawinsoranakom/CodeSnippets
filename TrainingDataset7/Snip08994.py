def __init__(self, stream_or_string, **options):
        if not isinstance(stream_or_string, (bytes, str)):
            stream_or_string = stream_or_string.read()
        if isinstance(stream_or_string, bytes):
            stream_or_string = stream_or_string.decode()
        try:
            objects = json.loads(stream_or_string)
        except Exception as exc:
            raise DeserializationError() from exc
        super().__init__(objects, **options)