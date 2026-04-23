def __init__(self, *, protocol="both", unpack_ipv4=False, **kwargs):
        self.unpack_ipv4 = unpack_ipv4
        self.default_validators = validators.ip_address_validators(
            protocol, unpack_ipv4
        )
        kwargs.setdefault("max_length", MAX_IPV6_ADDRESS_LENGTH)
        super().__init__(**kwargs)