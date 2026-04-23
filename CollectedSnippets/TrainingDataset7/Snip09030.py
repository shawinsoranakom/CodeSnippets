def __init__(self, stream_or_string, **options):
        stream = stream_or_string
        if isinstance(stream_or_string, bytes):
            stream = stream_or_string.decode()
        try:
            objects = yaml.load(stream, Loader=SafeLoader)
        except Exception as exc:
            raise DeserializationError() from exc
        super().__init__(objects, **options)