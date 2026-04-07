def __init__(self, stream_or_string, **options):
        if isinstance(stream_or_string, bytes):
            stream_or_string = stream_or_string.decode()
        if isinstance(stream_or_string, str):
            stream_or_string = stream_or_string.splitlines()
        super().__init__(Deserializer._get_lines(stream_or_string), **options)