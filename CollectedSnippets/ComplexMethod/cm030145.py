def _parse_mac(word):
    # Accept 'HH:HH:HH:HH:HH:HH' MAC address (ex: '52:54:00:9d:0e:67'),
    # but reject IPv6 address (ex: 'fe80::5054:ff:fe9' or '123:2:3:4:5:6:7:8').
    #
    # Virtual interfaces, such as those provided by VPNs, do not have a
    # colon-delimited MAC address as expected, but a 16-byte HWAddr separated
    # by dashes. These should be ignored in favor of a real MAC address
    parts = word.split(_MAC_DELIM)
    if len(parts) != 6:
        return
    if _MAC_OMITS_LEADING_ZEROES:
        # (Only) on AIX the macaddr value given is not prefixed by 0, e.g.
        # en0   1500  link#2      fa.bc.de.f7.62.4 110854824     0 160133733     0     0
        # not
        # en0   1500  link#2      fa.bc.de.f7.62.04 110854824     0 160133733     0     0
        if not all(1 <= len(part) <= 2 for part in parts):
            return
        hexstr = b''.join(part.rjust(2, b'0') for part in parts)
    else:
        if not all(len(part) == 2 for part in parts):
            return
        hexstr = b''.join(parts)
    try:
        return int(hexstr, 16)
    except ValueError:
        return