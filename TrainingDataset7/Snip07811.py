def __init__(self, name, locale, *, provider="libc", deterministic=True):
        self.name = name
        self.locale = locale
        self.provider = provider
        self.deterministic = deterministic