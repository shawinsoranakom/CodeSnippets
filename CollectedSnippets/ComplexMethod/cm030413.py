def get_payload(self, i=None, decode=False):
        """Return a reference to the payload.

        The payload will either be a list object or a string.  If you mutate
        the list object, you modify the message's payload in place.  Optional
        i returns that index into the payload.

        Optional decode is a flag indicating whether the payload should be
        decoded or not, according to the Content-Transfer-Encoding header
        (default is False).

        When True and the message is not a multipart, the payload will be
        decoded if this header's value is `quoted-printable' or `base64'.  If
        some other encoding is used, or the header is missing, or if the
        payload has bogus data (i.e. bogus base64 or uuencoded data), the
        payload is returned as-is.

        If the message is a multipart and the decode flag is True, then None
        is returned.
        """
        # Here is the logic table for this code, based on the email5.0.0 code:
        #   i     decode  is_multipart  result
        # ------  ------  ------------  ------------------------------
        #  None   True    True          None
        #   i     True    True          None
        #  None   False   True          _payload (a list)
        #   i     False   True          _payload element i (a Message)
        #   i     False   False         error (not a list)
        #   i     True    False         error (not a list)
        #  None   False   False         _payload
        #  None   True    False         _payload decoded (bytes)
        # Note that Barry planned to factor out the 'decode' case, but that
        # isn't so easy now that we handle the 8 bit data, which needs to be
        # converted in both the decode and non-decode path.
        if self.is_multipart():
            if decode:
                return None
            if i is None:
                return self._payload
            else:
                return self._payload[i]
        # For backward compatibility, Use isinstance and this error message
        # instead of the more logical is_multipart test.
        if i is not None and not isinstance(self._payload, list):
            raise TypeError('Expected list, got %s' % type(self._payload))
        payload = self._payload
        cte = self.get('content-transfer-encoding', '')
        if hasattr(cte, 'cte'):
            cte = cte.cte
        else:
            # cte might be a Header, so for now stringify it.
            cte = str(cte).strip().lower()
        # payload may be bytes here.
        if not decode:
            if isinstance(payload, str) and utils._has_surrogates(payload):
                try:
                    bpayload = payload.encode('ascii', 'surrogateescape')
                    try:
                        payload = bpayload.decode(self.get_content_charset('ascii'), 'replace')
                    except LookupError:
                        payload = bpayload.decode('ascii', 'replace')
                except UnicodeEncodeError:
                    pass
            return payload
        if isinstance(payload, str):
            try:
                bpayload = payload.encode('ascii', 'surrogateescape')
            except UnicodeEncodeError:
                # This won't happen for RFC compliant messages (messages
                # containing only ASCII code points in the unicode input).
                # If it does happen, turn the string into bytes in a way
                # guaranteed not to fail.
                bpayload = payload.encode('raw-unicode-escape')
        else:
            bpayload = payload
        if cte == 'quoted-printable':
            return quopri.decodestring(bpayload)
        elif cte == 'base64':
            # XXX: this is a bit of a hack; decode_b should probably be factored
            # out somewhere, but I haven't figured out where yet.
            value, defects = decode_b(b''.join(bpayload.splitlines()))
            for defect in defects:
                self.policy.handle_defect(self, defect)
            return value
        elif cte in ('x-uuencode', 'uuencode', 'uue', 'x-uue'):
            try:
                return _decode_uu(bpayload)
            except ValueError:
                # Some decoding problem.
                return bpayload
        if isinstance(payload, str):
            return bpayload
        return payload