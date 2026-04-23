def _winrm_connect(self) -> winrm.Protocol:
        """
        Establish a WinRM connection over HTTP/HTTPS.
        """
        display.vvv("ESTABLISH WINRM CONNECTION FOR USER: %s on PORT %s TO %s" %
                    (self._winrm_user, self._winrm_port, self._winrm_host), host=self._winrm_host)

        winrm_host = self._winrm_host
        if HAS_IPADDRESS:
            display.debug("checking if winrm_host %s is an IPv6 address" % winrm_host)
            try:
                ipaddress.IPv6Address(winrm_host)
            except ipaddress.AddressValueError:
                pass
            else:
                winrm_host = "[%s]" % winrm_host

        netloc = '%s:%d' % (winrm_host, self._winrm_port)
        endpoint = urlunsplit((self._winrm_scheme, netloc, self._winrm_path, '', ''))
        errors = []
        for transport in self._winrm_transport:
            if transport == 'kerberos':
                if not HAVE_KERBEROS:
                    kerb_msg = (
                        'WinRM Kerberos authentication requested but the python kerberos library is not installed. '
                        'Please install the pykerberos library, set a different authentication method with ansible_winrm_transport, '
                        'or use a local user account to connect using basic authentication.'
                    )
                    errors.append(kerb_msg)
                    continue
                if self._kerb_managed:
                    self._kerb_auth(self._winrm_user, self._winrm_pass)
            display.vvvvv('WINRM CONNECT: transport=%s endpoint=%s' % (transport, endpoint), host=self._winrm_host)
            try:
                winrm_kwargs = self._winrm_kwargs.copy()
                if self._winrm_connection_timeout:
                    winrm_kwargs['operation_timeout_sec'] = self._winrm_connection_timeout
                    winrm_kwargs['read_timeout_sec'] = self._winrm_connection_timeout + 10
                protocol = Protocol(endpoint, transport=transport, **winrm_kwargs)

                # open the shell from connect so we know we're able to talk to the server
                if not self.shell_id:
                    self.shell_id = protocol.open_shell(codepage=65001)  # UTF-8
                    display.vvvvv('WINRM OPEN SHELL: %s' % self.shell_id, host=self._winrm_host)

                return protocol
            except Exception as e:
                err_msg = to_text(e).strip()
                if re.search(to_text(r'Operation\s+?timed\s+?out'), err_msg, re.I):
                    raise AnsibleError('the connection attempt timed out')
                m = re.search(to_text(r'Code\s+?(\d{3})'), err_msg)
                if m:
                    code = int(m.groups()[0])
                    if code == 401:
                        err_msg = 'the specified credentials were rejected by the server'
                    elif code == 411:
                        return protocol
                errors.append(u'%s: %s' % (transport, err_msg))
                display.vvvvv(u'WINRM CONNECTION ERROR: %s\n%s' % (err_msg, to_text(traceback.format_exc())), host=self._winrm_host)
        if errors:
            raise AnsibleConnectionFailure(', '.join(map(to_native, errors)))
        else:
            raise AnsibleError('No transport found for WinRM connection')