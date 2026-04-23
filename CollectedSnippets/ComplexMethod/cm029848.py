def _connect(self):
        # Create unique tag for this session,
        # and compile tagged response matcher.

        self.tagpre = Int2AP(random.randint(4096, 65535))
        self.tagre = re.compile(br'(?P<tag>'
                        + self.tagpre
                        + br'\d+) (?P<type>[A-Z]+) (?P<data>.*)', re.ASCII)

        # Get server welcome message,
        # request and store CAPABILITY response.

        if __debug__:
            self._cmd_log_len = 10
            self._cmd_log_idx = 0
            self._cmd_log = {}           # Last '_cmd_log_len' interactions
            if self.debug >= 1:
                self._mesg('new IMAP4 connection, tag=%s' % self.tagpre)

        self.welcome = self._get_response()
        if 'PREAUTH' in self.untagged_responses:
            self.state = 'AUTH'
        elif 'OK' in self.untagged_responses:
            self.state = 'NONAUTH'
        else:
            raise self.error(self.welcome)

        self._get_capabilities()
        if __debug__:
            if self.debug >= 3:
                self._mesg('CAPABILITIES: %r' % (self.capabilities,))

        for version in AllowedVersions:
            if not version in self.capabilities:
                continue
            self.PROTOCOL_VERSION = version
            return

        raise self.error('server not IMAP4 compliant')