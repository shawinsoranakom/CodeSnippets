def __setitem__(self, name, val):
        # Per RFC 2046 Section 5.2.1, message/rfc822 attachment headers must be
        # ASCII.
        name, val = forbid_multi_line_headers(name, val, "ascii")
        MIMEMessage.__setitem__(self, name, val)