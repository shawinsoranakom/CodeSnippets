def __init__(
        self,
        verbose_name=None,
        name=None,
        protocol="both",
        unpack_ipv4=False,
        *args,
        **kwargs,
    ):
        self.unpack_ipv4 = unpack_ipv4
        self.protocol = protocol
        self.default_validators = validators.ip_address_validators(
            protocol, unpack_ipv4
        )
        kwargs["max_length"] = MAX_IPV6_ADDRESS_LENGTH
        super().__init__(verbose_name, name, *args, **kwargs)