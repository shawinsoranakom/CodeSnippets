def decrypt(
        self,
        context: RequestContext,
        ciphertext_blob: CiphertextType | None = None,
        encryption_context: EncryptionContextType | None = None,
        grant_tokens: GrantTokenList | None = None,
        key_id: KeyIdType | None = None,
        encryption_algorithm: EncryptionAlgorithmSpec | None = None,
        recipient: RecipientInfo | None = None,
        dry_run: NullableBooleanType | None = None,
        dry_run_modifiers: DryRunModifierList | None = None,
        **kwargs,
    ) -> DecryptResponse:
        # In AWS, key_id is only supplied for data encrypted with an asymmetrical algorithm. For symmetrical
        # encryption, key_id is taken from the encrypted data itself.
        # Since LocalStack doesn't currently do asymmetrical encryption, there is a question of modeling here: we
        # currently expect data to be only encrypted with symmetric encryption, so having key_id inside. It might not
        # always be what customers expect.
        if key_id:
            account_id, region_name, key_id = self._parse_key_id(key_id, context)
            try:
                ciphertext = deserialize_ciphertext_blob(ciphertext_blob=ciphertext_blob)
            except Exception as e:
                logging.error("Error deserializing ciphertext blob: %s", e)
                ciphertext = None
                pass
        else:
            try:
                ciphertext = deserialize_ciphertext_blob(ciphertext_blob=ciphertext_blob)
                account_id, region_name, key_id = self._parse_key_id(ciphertext.key_id, context)
            except Exception:
                raise InvalidCiphertextException(
                    "LocalStack is unable to deserialize the ciphertext blob. Perhaps the "
                    "blob didn't come from LocalStack"
                )

        key = self._get_kms_key(account_id, region_name, key_id)
        if ciphertext and key.metadata["KeyId"] != ciphertext.key_id:
            raise IncorrectKeyException(
                "The key ID in the request does not identify a CMK that can perform this operation."
            )

        self._validate_key_for_encryption_decryption(context, key)
        self._validate_key_state_not_pending_import(key)

        # Handle the recipient field.  This is used by AWS Nitro to re-encrypt the plaintext to the key specified
        # by the enclave.  Proper support for this will take significant work to figure out how to model enforcing
        # the attestation measurements; for now, if recipient is specified and has an attestation doc in it including
        # a public key where it's expected to be, we encrypt to that public key.  This at least allows users to use
        # localstack as a drop-in replacement for AWS when testing without having to skip the secondary decryption
        # when using localstack.
        recipient_pubkey = None
        if recipient:
            attestation_document = recipient["AttestationDocument"]
            # We do all of this in a try/catch and warn if it fails so that if users are currently passing a nonsense
            # value we don't break it for them.  In the future we could do a breaking change to require a valid attestation
            # (or at least one that contains the public key).
            try:
                recipient_pubkey = self._extract_attestation_pubkey(attestation_document)
            except Exception as e:
                logging.warning(
                    "Unable to extract public key from non-empty attestation document: %s", e
                )

        try:
            # TODO: Extend the implementation to handle additional encryption/decryption scenarios
            # beyond the current support for offline encryption and online decryption using RSA keys if key id exists in
            # parameters, where `ciphertext_blob` will not be deserializable.
            if self._is_rsa_spec(key.crypto_key.key_spec) and not ciphertext:
                plaintext = key.decrypt_rsa(ciphertext_blob)
            else:
                # if symmetric encryption then ciphertext must not be None
                if ciphertext is None:
                    raise InvalidCiphertextException()
                plaintext = key.decrypt(ciphertext, encryption_context)
        except InvalidTag:
            raise InvalidCiphertextException()

        # For compatibility, we return EncryptionAlgorithm values expected from AWS. But LocalStack currently always
        # encrypts with symmetric encryption no matter the key settings.
        #
        # We return a key ARN instead of KeyId despite the name of the parameter, as this is what AWS does and states
        # in its docs.
        #  https://docs.aws.amazon.com/kms/latest/APIReference/API_Decrypt.html#API_Decrypt_RequestSyntax
        # TODO add support for "dry_run"
        response = DecryptResponse(
            KeyId=key.metadata.get("Arn"),
            EncryptionAlgorithm=encryption_algorithm,
        )

        # Encrypt to the recipient pubkey if specified.  Otherwise, return the actual plaintext
        if recipient_pubkey:
            response["CiphertextForRecipient"] = pkcs7_envelope_encrypt(plaintext, recipient_pubkey)
        else:
            response["Plaintext"] = plaintext

        return response