def __init__(self, display_name='', username='', domain='', addr_spec=None):
        """Create an object representing a full email address.

        An address can have a 'display_name', a 'username', and a 'domain'.  In
        addition to specifying the username and domain separately, they may be
        specified together by using the addr_spec keyword *instead of* the
        username and domain keywords.  If an addr_spec string is specified it
        must be properly quoted according to RFC 5322 rules; an error will be
        raised if it is not.

        An Address object has display_name, username, domain, and addr_spec
        attributes, all of which are read-only.  The addr_spec and the string
        value of the object are both quoted according to RFC5322 rules, but
        without any Content Transfer Encoding.

        """

        inputs = ''.join(filter(None, (display_name, username, domain, addr_spec)))
        if '\r' in inputs or '\n' in inputs:
            raise ValueError("invalid arguments; address parts cannot contain CR or LF")

        # This clause with its potential 'raise' may only happen when an
        # application program creates an Address object using an addr_spec
        # keyword.  The email library code itself must always supply username
        # and domain.
        if addr_spec is not None:
            if username or domain:
                raise TypeError("addrspec specified when username and/or "
                                "domain also specified")
            a_s, rest = parser.get_addr_spec(addr_spec)
            if rest:
                raise ValueError("Invalid addr_spec; only '{}' "
                                 "could be parsed from '{}'".format(
                                    a_s, addr_spec))
            if a_s.all_defects:
                raise a_s.all_defects[0]
            username = a_s.local_part
            domain = a_s.domain
        self._display_name = display_name
        self._username = username
        self._domain = domain