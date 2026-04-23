def decrypt_and_get_vault_id(self, vaulttext):
        """Decrypt a piece of vault encrypted data.

        :arg vaulttext: a string to decrypt.  Since vault encrypted data is an
            ascii text format this can be either a byte str or unicode string.
        :returns: a byte string containing the decrypted data and the vault-id vault-secret that was used
        """
        origin = Origin.get_tag(vaulttext)

        b_vaulttext = to_bytes(vaulttext, nonstring='error')  # enforce vaulttext is str/bytes, keep type check if removing type conversion

        if self.secrets is None:
            raise AnsibleVaultError("A vault password must be specified to decrypt data.", obj=vaulttext)

        if not is_encrypted(b_vaulttext):
            raise AnsibleVaultError("Input is not vault encrypted data.", obj=vaulttext)

        b_vaulttext, dummy, cipher_name, vault_id = parse_vaulttext_envelope(b_vaulttext)

        # create the cipher object, note that the cipher used for decrypt can
        # be different than the cipher used for encrypt
        if cipher_name in CIPHER_ALLOWLIST:
            this_cipher = CIPHER_MAPPING[cipher_name]()
        else:
            raise AnsibleVaultError(f"Cipher {cipher_name!r} could not be found.", obj=vaulttext)

        if not self.secrets:
            raise AnsibleVaultError('Attempting to decrypt but no vault secrets found.', obj=vaulttext)

        # WARNING: Currently, the vault id is not required to match the vault id in the vault blob to
        #          decrypt a vault properly. The vault id in the vault blob is not part of the encrypted
        #          or signed vault payload. There is no cryptographic checking/verification/validation of the
        #          vault blobs vault id. It can be tampered with and changed. The vault id is just a nick
        #          name to use to pick the best secret and provide some ux/ui info.

        # iterate over all the applicable secrets (all of them by default) until one works...
        # if we specify a vault_id, only the corresponding vault secret is checked and
        # we check it first.

        vault_id_matchers = []

        if vault_id:
            display.vvvvv(u'Found a vault_id (%s) in the vaulttext' % to_text(vault_id))
            vault_id_matchers.append(vault_id)
            _matches = match_secrets(self.secrets, vault_id_matchers)
            if _matches:
                display.vvvvv(u'We have a secret associated with vault id (%s), will try to use to decrypt %s' % (to_text(vault_id), to_text(origin)))
            else:
                display.vvvvv(u'Found a vault_id (%s) in the vault text, but we do not have a associated secret (--vault-id)' % to_text(vault_id))

        # Not adding the other secrets to vault_secret_ids enforces a match between the vault_id from the vault_text and
        # the known vault secrets.
        if not C.DEFAULT_VAULT_ID_MATCH:
            # Add all of the known vault_ids as candidates for decrypting a vault.
            vault_id_matchers.extend([_vault_id for _vault_id, _dummy in self.secrets if _vault_id != vault_id])

        matched_secrets = match_secrets(self.secrets, vault_id_matchers)

        # for vault_secret_id in vault_secret_ids:
        for vault_secret_id, vault_secret in matched_secrets:
            display.vvvvv(u'Trying to use vault secret=(%s) id=%s to decrypt %s' % (to_text(vault_secret), to_text(vault_secret_id), to_text(origin)))

            try:
                # secret = self.secrets[vault_secret_id]
                display.vvvv(u'Trying secret %s for vault_id=%s' % (to_text(vault_secret), to_text(vault_secret_id)))
                b_plaintext = this_cipher.decrypt(b_vaulttext, vault_secret)
                # DTFIX7: possible candidate for propagate_origin
                b_plaintext = AnsibleTagHelper.tag_copy(vaulttext, b_plaintext)
                if b_plaintext is not None:
                    vault_id_used = vault_secret_id
                    vault_secret_used = vault_secret
                    file_slug = ''
                    if origin:
                        file_slug = ' of "%s"' % origin
                    display.vvvvv(
                        u'Decrypt%s successful with secret=%s and vault_id=%s' % (to_text(file_slug), to_text(vault_secret), to_text(vault_secret_id))
                    )
                    break
            except AnsibleVaultFormatError:
                raise
            except AnsibleError as e:
                display.vvvv(u'Tried to use the vault secret (%s) to decrypt (%s) but it failed. Error: %s' %
                             (to_text(vault_secret_id), to_text(origin), e))
                continue
        else:
            raise AnsibleVaultError("Decryption failed (no vault secrets were found that could decrypt).", obj=vaulttext)

        return b_plaintext, vault_id_used, vault_secret_used