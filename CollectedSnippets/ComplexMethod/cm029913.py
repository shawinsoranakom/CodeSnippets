def _ip_int_from_string(cls, ip_str):
        """Turn an IPv6 ip_str into an integer.

        Args:
            ip_str: A string, the IPv6 ip_str.

        Returns:
            An int, the IPv6 address

        Raises:
            AddressValueError: if ip_str isn't a valid IPv6 Address.

        """
        if not ip_str:
            raise AddressValueError('Address cannot be empty')
        if len(ip_str) > 45:
            shorten = ip_str
            if len(shorten) > 100:
                shorten = f'{ip_str[:45]}({len(ip_str)-90} chars elided){ip_str[-45:]}'
            raise AddressValueError(f"At most 45 characters expected in "
                                    f"{shorten!r}")

        # We want to allow more parts than the max to be 'split'
        # to preserve the correct error message when there are
        # too many parts combined with '::'
        _max_parts = cls._HEXTET_COUNT + 1
        parts = ip_str.split(':', maxsplit=_max_parts)

        # An IPv6 address needs at least 2 colons (3 parts).
        _min_parts = 3
        if len(parts) < _min_parts:
            msg = "At least %d parts expected in %r" % (_min_parts, ip_str)
            raise AddressValueError(msg)

        # If the address has an IPv4-style suffix, convert it to hexadecimal.
        if '.' in parts[-1]:
            try:
                ipv4_int = IPv4Address(parts.pop())._ip
            except AddressValueError as exc:
                raise AddressValueError("%s in %r" % (exc, ip_str)) from None
            parts.append('%x' % ((ipv4_int >> 16) & 0xFFFF))
            parts.append('%x' % (ipv4_int & 0xFFFF))

        # An IPv6 address can't have more than 8 colons (9 parts).
        # The extra colon comes from using the "::" notation for a single
        # leading or trailing zero part.
        if len(parts) > _max_parts:
            msg = "At most %d colons permitted in %r" % (_max_parts-1, ip_str)
            raise AddressValueError(msg)

        # Disregarding the endpoints, find '::' with nothing in between.
        # This indicates that a run of zeroes has been skipped.
        skip_index = None
        for i in range(1, len(parts) - 1):
            if not parts[i]:
                if skip_index is not None:
                    # Can't have more than one '::'
                    msg = "At most one '::' permitted in %r" % ip_str
                    raise AddressValueError(msg)
                skip_index = i

        # parts_hi is the number of parts to copy from above/before the '::'
        # parts_lo is the number of parts to copy from below/after the '::'
        if skip_index is not None:
            # If we found a '::', then check if it also covers the endpoints.
            parts_hi = skip_index
            parts_lo = len(parts) - skip_index - 1
            if not parts[0]:
                parts_hi -= 1
                if parts_hi:
                    msg = "Leading ':' only permitted as part of '::' in %r"
                    raise AddressValueError(msg % ip_str)  # ^: requires ^::
            if not parts[-1]:
                parts_lo -= 1
                if parts_lo:
                    msg = "Trailing ':' only permitted as part of '::' in %r"
                    raise AddressValueError(msg % ip_str)  # :$ requires ::$
            parts_skipped = cls._HEXTET_COUNT - (parts_hi + parts_lo)
            if parts_skipped < 1:
                msg = "Expected at most %d other parts with '::' in %r"
                raise AddressValueError(msg % (cls._HEXTET_COUNT-1, ip_str))
        else:
            # Otherwise, allocate the entire address to parts_hi.  The
            # endpoints could still be empty, but _parse_hextet() will check
            # for that.
            if len(parts) != cls._HEXTET_COUNT:
                msg = "Exactly %d parts expected without '::' in %r"
                raise AddressValueError(msg % (cls._HEXTET_COUNT, ip_str))
            if not parts[0]:
                msg = "Leading ':' only permitted as part of '::' in %r"
                raise AddressValueError(msg % ip_str)  # ^: requires ^::
            if not parts[-1]:
                msg = "Trailing ':' only permitted as part of '::' in %r"
                raise AddressValueError(msg % ip_str)  # :$ requires ::$
            parts_hi = len(parts)
            parts_lo = 0
            parts_skipped = 0

        try:
            # Now, parse the hextets into a 128-bit integer.
            ip_int = 0
            for i in range(parts_hi):
                ip_int <<= 16
                ip_int |= cls._parse_hextet(parts[i])
            ip_int <<= 16 * parts_skipped
            for i in range(-parts_lo, 0):
                ip_int <<= 16
                ip_int |= cls._parse_hextet(parts[i])
            return ip_int
        except ValueError as exc:
            raise AddressValueError("%s in %r" % (exc, ip_str)) from None