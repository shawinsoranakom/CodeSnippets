def ip_address_validators(protocol, unpack_ipv4):
    """
    Depending on the given parameters, return the appropriate validators for
    the GenericIPAddressField.
    """
    if protocol != "both" and unpack_ipv4:
        raise ValueError(
            "You can only use `unpack_ipv4` if `protocol` is set to 'both'"
        )
    try:
        return ip_address_validator_map[protocol.lower()]
    except KeyError:
        raise ValueError(
            "The protocol '%s' is unknown. Supported: %s"
            % (protocol, list(ip_address_validator_map))
        )