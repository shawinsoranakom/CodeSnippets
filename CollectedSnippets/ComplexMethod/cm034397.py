def check_password_encrypted(self):
        # Darwin needs cleartext password, so skip validation
        if self.module.params['password'] and self.platform != 'Darwin':
            maybe_invalid = False

            # Allow setting certain passwords in order to disable the account
            if self.module.params['password'] in set(['*', '!', '*************']):
                maybe_invalid = False
            else:
                # : for delimiter, * for disable user, ! for lock user
                # these characters are invalid in the password
                if any(char in self.module.params['password'] for char in ':*!'):
                    maybe_invalid = True
                if '$' not in self.module.params['password']:
                    maybe_invalid = True
                else:
                    fields = self.module.params['password'].split("$")
                    if len(fields) >= 3:
                        # contains character outside the crypto constraint
                        if bool(_HASH_RE.search(fields[-1])):
                            maybe_invalid = True
                        # md5
                        if fields[1] == '1' and len(fields[-1]) != 22:
                            maybe_invalid = True
                        # sha256
                        if fields[1] == '5' and len(fields[-1]) != 43:
                            maybe_invalid = True
                        # sha512
                        if fields[1] == '6' and len(fields[-1]) != 86:
                            maybe_invalid = True
                        # yescrypt
                        if fields[1] == 'y' and len(fields[-1]) != 43:
                            maybe_invalid = True
                    else:
                        maybe_invalid = True
            if maybe_invalid:
                self.module.warn("The input password appears not to have been hashed. "
                                 "The 'password' argument must be encrypted for this module to work properly.")