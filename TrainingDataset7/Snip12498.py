def __init__(self, **kwargs):
        # The default maximum length of an email is 320 characters per RFC 3696
        # section 3.
        kwargs.setdefault("max_length", 320)
        super().__init__(strip=True, **kwargs)