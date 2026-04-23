def get_authorization(self, req, chal):
        try:
            realm = chal['realm']
            nonce = chal['nonce']
            qop = chal.get('qop')
            algorithm = chal.get('algorithm', 'MD5')
            # mod_digest doesn't send an opaque, even though it isn't
            # supposed to be optional
            opaque = chal.get('opaque', None)
        except KeyError:
            return None

        H, KD = self.get_algorithm_impls(algorithm)
        if H is None:
            return None

        user, pw = self.passwd.find_user_password(realm, req.full_url)
        if user is None:
            return None

        # XXX not implemented yet
        if req.data is not None:
            entdig = self.get_entity_digest(req.data, chal)
        else:
            entdig = None

        A1 = "%s:%s:%s" % (user, realm, pw)
        A2 = "%s:%s" % (req.get_method(),
                        # XXX selector: what about proxies and full urls
                        req.selector)
        # NOTE: As per  RFC 2617, when server sends "auth,auth-int", the client could use either `auth`
        #     or `auth-int` to the response back. we use `auth` to send the response back.
        if qop is None:
            respdig = KD(H(A1), "%s:%s" % (nonce, H(A2)))
        elif 'auth' in qop.split(','):
            if nonce == self.last_nonce:
                self.nonce_count += 1
            else:
                self.nonce_count = 1
                self.last_nonce = nonce
            ncvalue = '%08x' % self.nonce_count
            cnonce = self.get_cnonce(nonce)
            noncebit = "%s:%s:%s:%s:%s" % (nonce, ncvalue, cnonce, 'auth', H(A2))
            respdig = KD(H(A1), noncebit)
        else:
            # XXX handle auth-int.
            raise URLError("qop '%s' is not supported." % qop)

        # XXX should the partial digests be encoded too?

        base = 'username="%s", realm="%s", nonce="%s", uri="%s", ' \
               'response="%s"' % (user, realm, nonce, req.selector,
                                  respdig)
        if opaque:
            base += ', opaque="%s"' % opaque
        if entdig:
            base += ', digest="%s"' % entdig
        base += ', algorithm="%s"' % algorithm
        if qop:
            base += ', qop=auth, nc=%s, cnonce="%s"' % (ncvalue, cnonce)
        return base