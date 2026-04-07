def __init__(self, stream_or_string, **options):
        """
        Init this serializer given a stream or a string
        """
        self.options = options
        if isinstance(stream_or_string, str):
            self.stream = StringIO(stream_or_string)
        else:
            self.stream = stream_or_string