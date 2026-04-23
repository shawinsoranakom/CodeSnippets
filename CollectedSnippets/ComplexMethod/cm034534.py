def _hash(self, secret, salt, salt_size, rounds, ident):
        # Not every hash algorithm supports every parameter.
        # Thus create the settings dict only with set parameters.
        settings = {}
        if salt:
            settings['salt'] = salt
        if salt_size:
            settings['salt_size'] = salt_size
        if rounds:
            settings['rounds'] = rounds
        if ident:
            settings['ident'] = ident

        # starting with passlib 1.7 'using' and 'hash' should be used instead of 'encrypt'
        try:
            if hasattr(self.crypt_algo, 'hash'):
                result = self.crypt_algo.using(**settings).hash(secret)
            elif hasattr(self.crypt_algo, 'encrypt'):
                result = self.crypt_algo.encrypt(secret, **settings)
            else:
                raise ValueError(f"Installed passlib version {passlib.__version__} is not supported.")
        except ValueError as ex:
            raise AnsibleError("Could not hash the secret.") from ex

        # passlib.hash should always return something or raise an exception.
        # Still ensure that there is always a result.
        # Otherwise an empty password might be assumed by some modules, like the user module.
        if not result:
            raise AnsibleError(f"Failed to hash with passlib using the {self.algorithm!r} algorithm.")

        # Hashes from passlib.hash should be represented as ascii strings of hex
        # digits so this should not traceback.  If it's not representable as such
        # we need to traceback and then block such algorithms because it may
        # impact calling code.
        return to_text(result, errors='strict')