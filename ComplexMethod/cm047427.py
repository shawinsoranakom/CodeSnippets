def _connect__(self, host=None, port=None, user=None, password=None, encryption=None,  # noqa: PLW3201
                smtp_from=None, ssl_certificate=None, ssl_private_key=None, smtp_debug=False, mail_server_id=None,
                allow_archived=False):
        """Returns a new SMTP connection to the given SMTP server.
           When running in test mode, this method does nothing and returns `None`.

           :param host: host or IP of SMTP server to connect to, if mail_server_id not passed
           :param int port: SMTP port to connect to
           :param user: optional username to authenticate with
           :param password: optional password to authenticate with
           :param str encryption: optional, ``'none'`` | ``'ssl'`` | ``'ssl_strict'`` | ``'starttls'`` | ``'starttls_strict'``.
               The 'strict' variants verify the remote server's certificate against the operating system trust store.
           :param smtp_from: FROM SMTP envelop, used to find the best mail server
           :param ssl_certificate: filename of the SSL certificate used for authentication
               Used when no mail server is given and overwrite  the odoo-bin argument "smtp_ssl_certificate"
           :param ssl_private_key: filename of the SSL private key used for authentication
               Used when no mail server is given and overwrite  the odoo-bin argument "smtp_ssl_private_key"
           :param bool smtp_debug: toggle debugging of SMTP sessions (all i/o
                              will be output in logs)
           :param mail_server_id: ID of specific mail server to use (overrides other parameters)
           :param bool allow_archived: by default (False), an exception is raised when calling this method on an
               archived record (using mail_server_id param). It can be set to True for testing so that the exception is
               no longer raised.
        """
        # Do not actually connect while running in test mode
        if self._disable_send():
            return None
        mail_server = smtp_encryption = None
        if mail_server_id:
            mail_server = self.sudo().browse(mail_server_id)
            self._check_forced_mail_server(mail_server, allow_archived, smtp_from)

        elif not host:
            mail_server, smtp_from = self.sudo()._find_mail_server(smtp_from)

        if not mail_server:
            mail_server = self.env['ir.mail_server']
        ssl_context = None

        if mail_server and mail_server.smtp_authentication != "cli":
            smtp_server = mail_server.smtp_host
            smtp_port = mail_server.smtp_port
            if mail_server.smtp_authentication == "certificate":
                smtp_user = None
                smtp_password = None
            else:
                smtp_user = mail_server.smtp_user
                smtp_password = mail_server.smtp_pass
            smtp_encryption = mail_server.smtp_encryption
            smtp_debug = smtp_debug or mail_server.smtp_debug
            from_filter = mail_server.from_filter

            if mail_server.smtp_authentication == "certificate":
                try:
                    ssl_context = PyOpenSSLContext(ssl.PROTOCOL_TLS)
                    if mail_server.smtp_encryption in ('ssl_strict', 'starttls_strict'):
                        ssl_context.set_default_verify_paths()
                        ssl_context._ctx.set_verify(
                            VERIFY_PEER | VERIFY_FAIL_IF_NO_PEER_CERT,
                            functools.partial(_verify_check_hostname_callback, hostname=smtp_server)
                        )
                    else:  # ssl, starttls
                        ssl_context.verify_mode = ssl.CERT_NONE
                    ssl_context._ctx.use_certificate(load_pem_x509_certificate(
                        base64.b64decode(mail_server.smtp_ssl_certificate)))
                    ssl_context._ctx.use_privatekey(load_pem_private_key(
                        base64.b64decode(mail_server.smtp_ssl_private_key),
                        password=None))
                    # Check that the private key match the certificate
                    ssl_context._ctx.check_privatekey()
                except SSLCryptoError as e:
                    raise UserError(_('The private key or the certificate is not a valid file. \n%s', str(e)))
                except SSLError as e:
                    raise UserError(_('Could not load your certificate / private key. \n%s', str(e)))
            elif mail_server.smtp_encryption != 'none':
                if mail_server.smtp_encryption in ('ssl_strict', 'starttls_strict'):
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = True
                    ssl_context.verify_mode = ssl.CERT_REQUIRED
                else:  # ssl, starttls
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE

        else:
            # we were passed individual smtp parameters or nothing and there is no default server
            smtp_server = host or tools.config.get('smtp_server')
            smtp_port = tools.config.get('smtp_port', 25) if port is None else port
            smtp_user = user or tools.config.get('smtp_user')
            smtp_password = password or tools.config.get('smtp_password')
            if mail_server:
                from_filter = mail_server.from_filter
            else:
                from_filter = self.env['ir.mail_server']._get_default_from_filter()

            smtp_encryption = encryption
            if smtp_encryption is None and tools.config.get('smtp_ssl'):
                smtp_encryption = 'starttls' # smtp_ssl => STARTTLS as of v7
            smtp_ssl_certificate_filename = ssl_certificate or tools.config.get('smtp_ssl_certificate_filename')
            smtp_ssl_private_key_filename = ssl_private_key or tools.config.get('smtp_ssl_private_key_filename')

            if smtp_ssl_certificate_filename and smtp_ssl_private_key_filename:
                try:
                    ssl_context = PyOpenSSLContext(ssl.PROTOCOL_TLS)
                    ssl_context.verify_mode = ssl.CERT_NONE
                    ssl_context.load_cert_chain(smtp_ssl_certificate_filename, keyfile=smtp_ssl_private_key_filename)
                    # Check that the private key match the certificate
                    ssl_context._ctx.check_privatekey()
                except SSLCryptoError as e:
                    raise UserError(_('The private key or the certificate is not a valid file. \n%s', str(e)))
                except SSLError as e:
                    raise UserError(_('Could not load your certificate / private key. \n%s', str(e)))

        if not smtp_server:
            raise UserError(_(
                "Missing SMTP Server\n"
                "Please define at least one SMTP server, "
                "or provide the SMTP parameters explicitly.",
            ))

        if smtp_encryption in ('ssl', 'ssl_strict'):
            connection = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=SMTP_TIMEOUT, context=ssl_context)
        else:
            connection = smtplib.SMTP(smtp_server, smtp_port, timeout=SMTP_TIMEOUT)
        connection.set_debuglevel(smtp_debug)
        if smtp_encryption in ('starttls', 'starttls_strict'):
            # starttls() will perform ehlo() if needed first
            # and will discard the previous list of services
            # after successfully performing STARTTLS command,
            # (as per RFC 3207) so for example any AUTH
            # capability that appears only on encrypted channels
            # will be correctly detected for next step
            connection.starttls(context=ssl_context)

        if smtp_user:
            # Attempt authentication - will raise if AUTH service not supported
            local, at, domain = smtp_user.rpartition('@')
            if at:
                smtp_user = local + at + idna.encode(domain).decode('ascii')
            mail_server._smtp_login__(connection, smtp_user, smtp_password or '')

        # Some methods of SMTP don't check whether EHLO/HELO was sent.
        # Anyway, as it may have been sent by login(), all subsequent usages should consider this command as sent.
        connection.ehlo_or_helo_if_needed()

        # Store the "from_filter" of the mail server / odoo-bin argument to  know if we
        # need to change the FROM headers or not when we will prepare the mail message
        connection.from_filter = from_filter
        connection.smtp_from = smtp_from

        return connection