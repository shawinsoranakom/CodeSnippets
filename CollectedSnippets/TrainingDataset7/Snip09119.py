def __init__(self, **kwargs):
        self.accept_idna = kwargs.pop("accept_idna", True)

        if self.accept_idna:
            self.regex = _lazy_re_compile(
                r"^" + self.hostname_re + self.domain_re + self.tld_re + r"$",
                re.IGNORECASE,
            )
        else:
            self.regex = _lazy_re_compile(
                r"^"
                + self.ascii_only_hostname_re
                + self.ascii_only_domain_re
                + self.ascii_only_tld_re
                + r"$",
                re.IGNORECASE,
            )
        super().__init__(**kwargs)