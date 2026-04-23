def __format__(self, fmt):
        """Returns an IP address as a formatted string.

        Supported presentation types are:
        's': returns the IP address as a string (default)
        'b': converts to binary and returns a zero-padded string
        'X' or 'x': converts to upper- or lower-case hex and returns a zero-padded string
        'n': the same as 'b' for IPv4 and 'x' for IPv6

        For binary and hex presentation types, the alternate form specifier
        '#' and the grouping option '_' are supported.
        """

        # Support string formatting
        if not fmt or fmt[-1] == 's':
            return format(str(self), fmt)

        # From here on down, support for 'bnXx'
        global _address_fmt_re
        if _address_fmt_re is None:
            import re
            _address_fmt_re = re.compile('(#?)(_?)([xbnX])')

        m = _address_fmt_re.fullmatch(fmt)
        if not m:
            return super().__format__(fmt)

        alternate, grouping, fmt_base = m.groups()

        # Set some defaults
        if fmt_base == 'n':
            if self.version == 4:
                fmt_base = 'b'  # Binary is default for ipv4
            else:
                fmt_base = 'x'  # Hex is default for ipv6

        if fmt_base == 'b':
            padlen = self.max_prefixlen
        else:
            padlen = self.max_prefixlen // 4

        if grouping:
            padlen += padlen // 4 - 1

        if alternate:
            padlen += 2  # 0b or 0x

        return format(int(self), f'{alternate}0{padlen}{grouping}{fmt_base}')