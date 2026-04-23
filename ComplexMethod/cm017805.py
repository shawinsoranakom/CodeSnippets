def sanitize_address(addr, encoding):
    """
    Format a pair of (name, address) or an email address string.
    """
    warnings.warn(
        "The internal API sanitize_address() is deprecated."
        " Python's modern email API (with email.message.EmailMessage or"
        " email.policy.default) will handle most required validation and"
        " encoding. Use Python's email.headerregistry.Address to construct"
        " formatted addresses from component parts.",
        RemovedInDjango70Warning,
    )

    address = None
    if not isinstance(addr, tuple):
        addr = force_str(addr)
        try:
            token, rest = parser.get_mailbox(addr)
        except (HeaderParseError, ValueError, IndexError):
            raise ValueError('Invalid address "%s"' % addr)
        else:
            if rest:
                # The entire email address must be parsed.
                raise ValueError(
                    'Invalid address; only %s could be parsed from "%s"' % (token, addr)
                )
            nm = token.display_name or ""
            localpart = token.local_part
            domain = token.domain or ""
    else:
        nm, address = addr
        if "@" not in address:
            raise ValueError(f'Invalid address "{address}"')
        localpart, domain = address.rsplit("@", 1)

    address_parts = nm + localpart + domain
    if "\n" in address_parts or "\r" in address_parts:
        raise ValueError("Invalid address; address parts cannot contain newlines.")

    # Avoid UTF-8 encode, if it's possible.
    try:
        nm.encode("ascii")
        nm = Header(nm).encode()
    except UnicodeEncodeError:
        nm = Header(nm, encoding).encode()
    try:
        localpart.encode("ascii")
    except UnicodeEncodeError:
        localpart = Header(localpart, encoding).encode()
    domain = punycode(domain)

    parsed_address = Address(username=localpart, domain=domain)
    return formataddr((nm, parsed_address.addr_spec))