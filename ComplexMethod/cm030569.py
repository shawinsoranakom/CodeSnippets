def smtp_AUTH(self, arg):
        if not self.seen_greeting:
            self.push('503 Error: send EHLO first')
            return
        if not self.extended_smtp or 'AUTH' not in self._extrafeatures:
            self.push('500 Error: command "AUTH" not recognized')
            return
        if self.authenticated_user is not None:
            self.push(
                '503 Bad sequence of commands: already authenticated')
            return
        args = arg.split()
        if len(args) not in [1, 2]:
            self.push('501 Syntax: AUTH <mechanism> [initial-response]')
            return
        auth_object_name = '_auth_%s' % args[0].lower().replace('-', '_')
        try:
            self.auth_object = getattr(self, auth_object_name)
        except AttributeError:
            self.push('504 Command parameter not implemented: unsupported '
                      ' authentication mechanism {!r}'.format(auth_object_name))
            return
        self.smtp_state = self.AUTH
        self.auth_object(args[1] if len(args) == 2 else None)