def __init__(self, query_string=None, mutable=False, encoding=None):
        super().__init__()
        self.encoding = encoding or settings.DEFAULT_CHARSET
        query_string = query_string or ""
        parse_qsl_kwargs = {
            "keep_blank_values": True,
            "encoding": self.encoding,
            "max_num_fields": settings.DATA_UPLOAD_MAX_NUMBER_FIELDS,
        }
        if isinstance(query_string, bytes):
            # query_string normally contains URL-encoded data, a subset of
            # ASCII.
            try:
                query_string = query_string.decode(self.encoding)
            except UnicodeDecodeError:
                # ... but some user agents are misbehaving :-(
                query_string = query_string.decode("iso-8859-1")
        try:
            for key, value in parse_qsl(query_string, **parse_qsl_kwargs):
                self.appendlist(key, value)
        except ValueError as e:
            # ValueError can also be raised if the strict_parsing argument to
            # parse_qsl() is True. As that is not used by Django, assume that
            # the exception was raised by exceeding the value of max_num_fields
            # instead of fragile checks of exception message strings.
            raise TooManyFieldsSent(
                "The number of GET/POST parameters exceeded "
                "settings.DATA_UPLOAD_MAX_NUMBER_FIELDS."
            ) from e
        self._mutable = mutable