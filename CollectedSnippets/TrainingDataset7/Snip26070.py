def _apply_cpython_128110_workaround(message, msg_bytes):
    """
    Updates message in place to correct misparsed rfc2047 display-names in
    address headers caused by https://github.com/python/cpython/issues/128110.
    """
    from email.header import decode_header
    from email.headerregistry import AddressHeader
    from email.parser import BytesHeaderParser
    from email.utils import getaddresses

    def rfc2047_decode(s):
        # Decode using legacy decode_header() (which doesn't have the bug).
        return "".join(
            (
                segment
                if charset is None and isinstance(segment, str)
                else segment.decode(charset or "ascii")
            )
            for segment, charset in decode_header(s)
        )

    def build_address(name, address):
        if "@" in address:
            return Address(display_name=name, addr_spec=address)
        return Address(display_name=name, username=address, domain="")

    # This workaround only applies to messages parsed with a modern policy.
    assert not isinstance(message.policy, policy.Compat32)

    # Reparse with compat32 to get access to raw (undecoded) headers.
    raw_headers = BytesHeaderParser(policy=policy.compat32).parsebytes(msg_bytes)
    for header, modern_value in message.items():
        if not isinstance(modern_value, AddressHeader):
            # The bug only affects structured address headers.
            continue
        raw_value = raw_headers[header]
        if RFC2047_PREFIX in raw_value:
            # Headers should not appear more than once.
            assert len(message.get_all(header)) == 1
            # Reconstruct Address objects using legacy APIs.
            unfolded = raw_value.replace("\r\n", "").replace("\n", "")
            corrected_addresses = (
                build_address(rfc2047_decode(name), address)
                for name, address in getaddresses([unfolded])
            )
            message.replace_header(header, corrected_addresses)