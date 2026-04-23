def parse(
        cls,
        input: str,
        default_host: str,
        default_port: int,
    ) -> "HostAndPort":
        """
        Parse a `HostAndPort` from strings like:
            - 0.0.0.0:4566 -> host=0.0.0.0, port=4566
            - 0.0.0.0      -> host=0.0.0.0, port=`default_port`
            - :4566        -> host=`default_host`, port=4566
            - [::]:4566    -> host=[::], port=4566
            - [::1]        -> host=[::1], port=`default_port`
        """
        host, port = default_host, default_port

        # recognize IPv6 addresses (+ port)
        if input.startswith("["):
            ipv6_pattern = re.compile(r"^\[(?P<host>[^]]+)\](:(?P<port>\d+))?$")
            match = ipv6_pattern.match(input)

            if match:
                host = match.group("host")
                if not is_ipv6_address(host):
                    raise ValueError(
                        f"input looks like an IPv6 address (is enclosed in square brackets), but is not valid: {host}"
                    )
                port_s = match.group("port")
                if port_s:
                    port = cls._validate_port(port_s)
            else:
                raise ValueError(
                    f'input looks like an IPv6 address, but is invalid. Should be formatted "[ip]:port": {input}'
                )

        # recognize IPv4 address + port
        elif ":" in input:
            hostname, port_s = input.split(":", 1)
            if hostname.strip():
                host = hostname.strip()
            port = cls._validate_port(port_s)
        else:
            if input.strip():
                host = input.strip()

        # validation
        if port < 0 or port >= 2**16:
            raise ValueError("port out of range")

        return cls(host=host, port=port)