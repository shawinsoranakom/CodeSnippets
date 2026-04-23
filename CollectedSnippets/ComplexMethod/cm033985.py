def _kerb_auth(self, principal: str, password: str) -> None:
        if password is None:
            password = ""
        b_password = to_bytes(password, encoding='utf-8', errors='surrogate_or_strict')

        self._kerb_ccache = tempfile.NamedTemporaryFile()
        display.vvvvv("creating Kerberos CC at %s" % self._kerb_ccache.name)
        krb5ccname = "FILE:%s" % self._kerb_ccache.name
        os.environ["KRB5CCNAME"] = krb5ccname
        krb5env = dict(PATH=os.environ["PATH"], KRB5CCNAME=krb5ccname)

        # Add any explicit environment vars into the krb5env block
        kinit_env_vars = self.get_option('kinit_env_vars')
        for var in kinit_env_vars:
            if var not in krb5env and var in os.environ:
                krb5env[var] = os.environ[var]

        # Stores various flags to call with kinit, these could be explicit args set by 'ansible_winrm_kinit_args' OR
        # '-f' if kerberos delegation is requested (ansible_winrm_kerberos_delegation).
        kinit_cmdline = [self._kinit_cmd]
        kinit_args = self.get_option('kinit_args')
        if kinit_args:
            kinit_args = [to_text(a) for a in shlex.split(kinit_args) if a.strip()]
            kinit_cmdline.extend(kinit_args)

        elif boolean(self.get_option('_extras').get('ansible_winrm_kerberos_delegation', False)):
            kinit_cmdline.append('-f')

        kinit_cmdline.append(principal)

        display.vvvv(f"calling kinit for principal {principal}")

        # It is important to use start_new_session which spawns the process
        # with setsid() to avoid it inheriting the current tty. On macOS it
        # will force it to read from stdin rather than the tty.
        try:
            p = subprocess.Popen(
                kinit_cmdline,
                start_new_session=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=krb5env,
            )

        except OSError as err:
            err_msg = "Kerberos auth failure when calling kinit cmd " \
                      "'%s': %s" % (self._kinit_cmd, to_native(err))
            raise AnsibleConnectionFailure(err_msg)

        stdout, stderr = p.communicate(b_password + b'\n')
        rc = p.returncode

        if rc != 0:
            # one last attempt at making sure the password does not exist
            # in the output
            exp_msg = to_native(stderr.strip())
            exp_msg = exp_msg.replace(to_native(password), "<redacted>")

            err_msg = f"Kerberos auth failure for principal {principal}: {exp_msg}"
            raise AnsibleConnectionFailure(err_msg)

        display.vvvvv("kinit succeeded for principal %s" % principal)