def _parse_parameters(self, term):
        """Hacky parsing of params

        See https://github.com/ansible/ansible-modules-core/issues/1968#issuecomment-136842156
        and the first_found lookup For how we want to fix this later
        """
        first_split = term.split(' ', 1)
        if len(first_split) <= 1:
            # Only a single argument given, therefore it's a path
            relpath = term
            params = dict()
        else:
            relpath = first_split[0]
            params = parse_kv(first_split[1])
            if '_raw_params' in params:
                # Spaces in the path?
                relpath = u' '.join((relpath, params['_raw_params']))
                del params['_raw_params']

                # Check that we parsed the params correctly
                if not term.startswith(relpath):
                    # Likely, the user had a non parameter following a parameter.
                    # Reject this as a user typo
                    raise AnsibleError('Unrecognized value after key=value parameters given to password lookup')
            # No _raw_params means we already found the complete path when
            # we split it initially

        # Check for invalid parameters.  Probably a user typo
        invalid_params = frozenset(params.keys()).difference(VALID_PARAMS)
        if invalid_params:
            raise AnsibleError('Unrecognized parameter(s) given to password lookup: %s' % ', '.join(invalid_params))

        # update options with what we got
        if params:
            self.set_options(direct=params)

        # chars still might need more
        chars = params.get('chars', self.get_option('chars'))
        if chars and isinstance(chars, str):
            tmp_chars = []
            if u',,' in chars:
                tmp_chars.append(u',')
            tmp_chars.extend(c for c in chars.replace(u',,', u',').split(u',') if c)
            self.set_option('chars', tmp_chars)

        # return processed params
        for field in VALID_PARAMS:
            params[field] = self.get_option(field)

        return relpath, params