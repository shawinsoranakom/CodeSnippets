def encrypt(self, plaintext, secret=None, vault_id=None, salt=None):
        """Vault encrypt a piece of data.

        :arg plaintext: a text or byte string to encrypt.
        :returns: a utf-8 encoded byte str of encrypted data.  The string
            contains a header identifying this as vault encrypted data and
            formatted to newline terminated lines of 80 characters.  This is
            suitable for dumping as is to a vault file.

        If the string passed in is a text string, it will be encoded to UTF-8
        before encryption.
        """

        if secret is None:
            if self.secrets:
                dummy, secret = match_encrypt_secret(self.secrets)
            else:
                raise AnsibleVaultError("A vault password must be specified to encrypt data")

        b_plaintext = to_bytes(plaintext, errors='surrogate_or_strict')

        if is_encrypted(b_plaintext):
            raise AnsibleError("input is already encrypted")

        if not self.cipher_name or self.cipher_name not in CIPHER_WRITE_ALLOWLIST:
            self.cipher_name = u"AES256"

        try:
            this_cipher = CIPHER_MAPPING[self.cipher_name]()
        except KeyError:
            raise AnsibleError(u"{0} cipher could not be found".format(self.cipher_name))

        # encrypt data
        if vault_id:
            display.vvvvv(u'Encrypting with vault_id "%s" and vault secret %s' % (to_text(vault_id), to_text(secret)))
        else:
            display.vvvvv(u'Encrypting without a vault_id using vault secret %s' % to_text(secret))

        b_ciphertext = this_cipher.encrypt(b_plaintext, secret, salt)

        # format the data for output to the file
        b_vaulttext = format_vaulttext_envelope(b_ciphertext,
                                                self.cipher_name,
                                                vault_id=vault_id)
        return b_vaulttext