def _looks_like_an_ip_adress(address: Optional[str]) -> bool:
    if address is None:
        return False

    try:
        socket.inet_pton(socket.AF_INET, address)
        return True  # Yup, this is an IPv4 address!
    except (AttributeError, OSError):
        pass

    try:
        socket.inet_pton(socket.AF_INET6, address)
        return True  # Yup, this is an IPv6 address!
    except (AttributeError, OSError):
        pass

    # Nope, this is not an IP address.
    return False