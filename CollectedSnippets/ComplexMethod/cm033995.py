def _build_command(self, binary: str, subsystem: str, *other_args: bytes | str) -> list[bytes]:
        """
        Takes an executable (ssh, scp, sftp or wrapper) and optional extra arguments and returns the remote command
        wrapped in local ssh shell commands and ready for execution.

        :arg binary: actual executable to use to execute command.
        :arg subsystem: type of executable provided, ssh/sftp/scp, needed because wrappers for ssh might have diff names.
        :arg other_args: dict of, value pairs passed as arguments to the ssh binary
        """
        conn_password = self.get_option('password') or self._play_context.password
        pkcs11_provider = self.get_option("pkcs11_provider")
        password_mechanism = self.get_option('password_mechanism')

        #
        # First, the command to invoke
        #

        b_command = [to_bytes(binary, errors='surrogate_or_strict')]

        #
        # Next, additional arguments based on the configuration.
        #

        # pkcs11 mode allows the use of Smartcards or Yubikey devices
        if conn_password and pkcs11_provider:
            self._add_args(b_command,
                           (b"-o", b"KbdInteractiveAuthentication=no",
                            b"-o", b"PreferredAuthentications=publickey",
                            b"-o", b"PasswordAuthentication=no",
                            b'-o', to_bytes(u'PKCS11Provider=%s' % pkcs11_provider)),
                           u'Enable pkcs11')

        # sftp batch mode allows us to correctly catch failed transfers, but can
        # be disabled if the client side doesn't support the option. However,
        # sftp batch mode does not prompt for passwords so it must be disabled
        # if not using controlpersist and using password auth
        b_args: t.Iterable[bytes]
        if subsystem == 'sftp' and self.get_option('sftp_batch_mode'):
            if conn_password:
                b_args = [b'-o', b'BatchMode=no']
                self._add_args(b_command, b_args, u'disable batch mode for password auth')
            b_command += [b'-b', b'-']

        if (verbosity := self.get_option('verbosity')) > 0:
            b_command.append(b'-' + (b'v' * verbosity))

        # Next, we add ssh_args
        ssh_args = self.get_option('ssh_args')
        if ssh_args:
            b_args = [to_bytes(a, errors='surrogate_or_strict') for a in
                      self._split_ssh_args(ssh_args)]
            self._add_args(b_command, b_args, u"ansible.cfg set ssh_args")

        # Now we add various arguments that have their own specific settings defined in docs above.
        if self.get_option('host_key_checking') is False:
            b_args = (b"-o", b"StrictHostKeyChecking=no")
            self._add_args(b_command, b_args, u"ANSIBLE_HOST_KEY_CHECKING/host_key_checking disabled")

        self.port = self.get_option('port')
        if self.port is not None:
            b_args = (b"-o", b"Port=" + to_bytes(self.port, nonstring='simplerepr', errors='surrogate_or_strict'))
            self._add_args(b_command, b_args, u"ANSIBLE_REMOTE_PORT/remote_port/ansible_port set")

        if self.get_option('private_key'):
            try:
                key = self._populate_agent()
            except Exception as e:
                raise AnsibleAuthenticationFailure('Failed to add configured private key into ssh-agent.') from e
            b_args = (b'-o', b'IdentitiesOnly=yes', b'-o', to_bytes(f'IdentityFile="{key}"', errors='surrogate_or_strict'))
            self._add_args(b_command, b_args, "ANSIBLE_PRIVATE_KEY/private_key set")
        elif key := self.get_option('private_key_file'):
            b_args = (b"-o", b'IdentityFile="' + to_bytes(os.path.expanduser(key), errors='surrogate_or_strict') + b'"')
            self._add_args(b_command, b_args, u"ANSIBLE_PRIVATE_KEY_FILE/private_key_file/ansible_ssh_private_key_file set")

        if not conn_password:
            self._add_args(
                b_command, (
                    b"-o", b"KbdInteractiveAuthentication=no",
                    b"-o", b"PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey",
                    b"-o", b"PasswordAuthentication=no"
                ),
                u"ansible_password/ansible_ssh_password not set"
            )

        self.user = self.get_option('remote_user')
        if self.user:
            self._add_args(
                b_command,
                (b"-o", b'User="%s"' % to_bytes(self.user, errors='surrogate_or_strict')),
                u"ANSIBLE_REMOTE_USER/remote_user/ansible_user/user/-u set"
            )

        timeout = self.get_option('timeout')
        self._add_args(
            b_command,
            (b"-o", b"ConnectTimeout=" + to_bytes(timeout, errors='surrogate_or_strict', nonstring='simplerepr')),
            u"ANSIBLE_TIMEOUT/timeout set"
        )

        # Add in any common or binary-specific arguments from the PlayContext
        # (i.e. inventory or task settings or overrides on the command line).

        for opt in (u'ssh_common_args', u'{0}_extra_args'.format(subsystem)):
            attr = self.get_option(opt)
            if attr is not None:
                b_args = [to_bytes(a, errors='surrogate_or_strict') for a in self._split_ssh_args(attr)]
                self._add_args(b_command, b_args, u"Set %s" % opt)

        # Check if ControlPersist is enabled and add a ControlPath if one hasn't
        # already been set.

        controlpersist, controlpath = self._persistence_controls(b_command)

        if controlpersist:
            self._persistent = True

            if not controlpath:
                self.control_path_dir = self.get_option('control_path_dir')
                cpdir = unfrackpath(self.control_path_dir)
                b_cpdir = to_bytes(cpdir, errors='surrogate_or_strict')

                # The directory must exist and be writable.
                makedirs_safe(b_cpdir, 0o700)
                if not os.access(b_cpdir, os.W_OK):
                    raise AnsibleError("Cannot write to ControlPath %s" % to_native(cpdir))

                self.control_path = self.get_option('control_path')
                if not self.control_path:
                    self.control_path = self._create_control_path(
                        self.host,
                        self.port,
                        self.user
                    )
                b_args = (b"-o", b'ControlPath="%s"' % to_bytes(self.control_path % dict(directory=cpdir), errors='surrogate_or_strict'))
                self._add_args(b_command, b_args, u"found only ControlPersist; added ControlPath")

        if password_mechanism == "ssh_askpass":
            self._add_args(
                b_command,
                (b"-o", b"NumberOfPasswordPrompts=1"),
                "Restrict number of password prompts in case incorrect password is provided.",
            )

        # Finally, we add any caller-supplied extras.
        if other_args:
            b_command += [to_bytes(a) for a in other_args]

        return b_command