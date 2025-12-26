def decimal_to_ipv4(decimal_ipv4: int) -> str:

    if not (0 <= decimal_ipv4 <= 4294967295):
        raise ValueError("Invalid decimal IPv4 address")

    ip_parts = []
    for _ in range(4):
        ip_parts.append(str(decimal_ipv4 & 255))
        decimal_ipv4 >>= 8

    return ".".join(reversed(ip_parts))
