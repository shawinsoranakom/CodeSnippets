def http_error_401(self, req, fp, code, msg, headers):
            # If we've already attempted the auth and we've reached this again then there was a failure.
            if self._context:
                return

            parsed = urlparse(req.get_full_url())

            auth_header = self.get_auth_value(headers)
            if not auth_header:
                return
            auth_protocol, in_token = auth_header

            username = None
            if self.username:
                username = gssapi.Name(self.username, name_type=gssapi.NameType.user)

            if username and self.password:
                if not hasattr(gssapi.raw, 'acquire_cred_with_password'):
                    raise NotImplementedError("Platform GSSAPI library does not support "
                                              "gss_acquire_cred_with_password, cannot acquire GSSAPI credential with "
                                              "explicit username and password.")

                b_password = to_bytes(self.password, errors='surrogate_or_strict')
                cred = gssapi.raw.acquire_cred_with_password(username, b_password, usage='initiate').creds

            else:
                cred = gssapi.Credentials(name=username, usage='initiate')

            # Get the peer certificate for the channel binding token if possible (HTTPS). A bug on macOS causes the
            # authentication to fail when the CBT is present. Just skip that platform.
            cbt = None
            cert = getpeercert(fp, True)
            if cert and platform.system() != 'Darwin':
                cert_hash = get_channel_binding_cert_hash(cert)
                if cert_hash:
                    cbt = gssapi.raw.ChannelBindings(application_data=b"tls-server-end-point:" + cert_hash)

            # TODO: We could add another option that is set to include the port in the SPN if desired in the future.
            target = gssapi.Name("HTTP@%s" % parsed.hostname, gssapi.NameType.hostbased_service)
            self._context = gssapi.SecurityContext(usage="initiate", name=target, creds=cred, channel_bindings=cbt)

            resp = None
            while not self._context.complete:
                out_token = self._context.step(in_token)
                if not out_token:
                    break

                auth_header = '%s %s' % (auth_protocol, to_native(base64.b64encode(out_token)))
                req.add_unredirected_header('Authorization', auth_header)
                resp = self.parent.open(req)

                # The response could contain a token that the client uses to validate the server
                auth_header = self.get_auth_value(resp.headers)
                if not auth_header:
                    break
                in_token = auth_header[1]

            return resp