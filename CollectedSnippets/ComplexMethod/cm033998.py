def _sshpass_cmd(self) -> list[bytes]:
        # If we want to use sshpass for password authentication, we have to set up a pipe to
        # write the password to sshpass.
        conn_password = self.get_option('password') or self._play_context.password
        pkcs11_provider = self.get_option("pkcs11_provider")
        if not (self.get_option('password_mechanism') == 'sshpass' and (conn_password or pkcs11_provider)):
            return []

        if not self._sshpass_available():
            raise AnsibleError("to use the password_mechanism=sshpass, you must install the sshpass program")
        if not conn_password and pkcs11_provider:
            raise AnsibleError("to use pkcs11_provider you must specify a password/pin")

        self.sshpass_pipe = os.pipe()
        b_command = [b'sshpass', b'-d' + to_bytes(self.sshpass_pipe[0], nonstring='simplerepr', errors='surrogate_or_strict')]

        password_prompt = self.get_option('sshpass_prompt')
        if not password_prompt and pkcs11_provider:
            # Set default password prompt for pkcs11_provider to make it clear it's a PIN
            password_prompt = PKCS11_DEFAULT_PROMPT

        if password_prompt:
            b_command += [b'-P', to_bytes(password_prompt, errors='surrogate_or_strict')]
        return b_command