def _build_kwargs(self) -> None:
        self._psrp_host = self.get_option('remote_addr')
        self._psrp_user = self.get_option('remote_user')

        protocol = self.get_option('protocol')
        port = self.get_option('port')
        if protocol is None and port is None:
            protocol = 'https'
            port = 5986
        elif protocol is None:
            protocol = 'https' if int(port) != 5985 else 'http'
        elif port is None:
            port = 5986 if protocol == 'https' else 5985

        self._psrp_port = int(port)
        self._psrp_auth = self.get_option('auth')

        self._psrp_runspace_kwargs = dict(
            configuration_name=self.get_option('configuration_name'),
        )
        if no_profile := self.get_option('no_profile'):
            self._psrp_runspace_kwargs['no_profile'] = no_profile

        # cert validation can either be a bool or a path to the cert
        cert_validation = self.get_option('cert_validation')
        cert_trust_path = self.get_option('ca_cert')
        if cert_validation == 'ignore':
            psrp_cert_validation = False
        elif cert_trust_path is not None:
            psrp_cert_validation = cert_trust_path
        else:
            psrp_cert_validation = True

        self._psrp_conn_kwargs = dict(
            server=self._psrp_host,
            port=self._psrp_port,
            username=self._psrp_user,
            password=self.get_option('remote_password'),
            ssl=protocol == 'https',
            path=self.get_option('path'),
            auth=self._psrp_auth,
            cert_validation=psrp_cert_validation,
            connection_timeout=self.get_option('connection_timeout'),
            encryption=self.get_option('message_encryption'),
            proxy=self.get_option('proxy'),
            no_proxy=boolean(self.get_option('ignore_proxy')),
            max_envelope_size=self.get_option('max_envelope_size'),
            operation_timeout=self.get_option('operation_timeout'),
            read_timeout=self.get_option('read_timeout'),
            reconnection_retries=self.get_option('reconnection_retries'),
            reconnection_backoff=float(self.get_option('reconnection_backoff')),
            certificate_key_pem=self.get_option('certificate_key_pem'),
            certificate_pem=self.get_option('certificate_pem'),
            credssp_auth_mechanism=self.get_option('credssp_auth_mechanism'),
            credssp_disable_tlsv1_2=self.get_option('credssp_disable_tlsv1_2'),
            credssp_minimum_version=self.get_option('credssp_minimum_version'),
            negotiate_send_cbt=self.get_option('negotiate_send_cbt'),
            negotiate_delegate=self.get_option('negotiate_delegate'),
            negotiate_hostname_override=self.get_option('negotiate_hostname_override'),
            negotiate_service=self.get_option('negotiate_service'),
        )

        # We don't always set this in case we are working with an older pypsrp
        # version that doesn't support this option.
        certificate_key_password = self.get_option('certificate_key_password')
        if certificate_key_password:
            self._psrp_conn_kwargs['certificate_key_password'] = certificate_key_password