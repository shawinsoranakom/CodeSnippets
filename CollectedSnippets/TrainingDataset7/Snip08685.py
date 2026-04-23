def _idna_encode_address_header_domains(self, msg):
        """
        If msg.policy does not permit utf8 in headers, IDNA encode all
        non-ASCII domains in its address headers.
        """
        # Avoids a problem where Python's email incorrectly converts non-ASCII
        # domains to RFC 2047 encoded-words:
        # https://github.com/python/cpython/issues/83938.
        # This applies to the domain only, not to the localpart (username).
        # There is no RFC that permits any 7-bit encoding for non-ASCII
        # characters before the '@'.
        if not getattr(msg.policy, "utf8", False):
            # Not using SMTPUTF8, so apply IDNA encoding in all address
            # headers. IDNA encoding does not alter domains that are already
            # ASCII.
            for field, value in msg.items():
                if isinstance(value, AddressHeader) and any(
                    not addr.domain.isascii() for addr in value.addresses
                ):
                    msg.replace_header(
                        field,
                        [
                            Address(
                                display_name=addr.display_name,
                                username=addr.username,
                                domain=punycode(addr.domain),
                            )
                            for addr in value.addresses
                        ],
                    )