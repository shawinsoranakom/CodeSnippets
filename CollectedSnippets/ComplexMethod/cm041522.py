def test_import_key_symmetric(self, kms_create_key, aws_client, snapshot):
        snapshot.add_transformer(snapshot.transform.key_value("Description"))
        key = kms_create_key(Origin="EXTERNAL")
        snapshot.match("created-key", key)
        key_id = key["KeyId"]

        # try key before importing
        plaintext = b"test content 123 !#"
        with pytest.raises(ClientError) as e:
            aws_client.kms.encrypt(Plaintext=plaintext, KeyId=key_id)
        snapshot.match("encrypt-before-import-error", e.value.response)

        # get key import params
        params = aws_client.kms.get_parameters_for_import(
            KeyId=key_id, WrappingAlgorithm="RSAES_OAEP_SHA_256", WrappingKeySpec="RSA_2048"
        )
        assert params["KeyId"] == key["Arn"]
        assert params["ImportToken"]
        assert params["PublicKey"]
        assert isinstance(params["ParametersValidTo"], datetime)

        # create 256 bit symmetric key (import_key_material(..) works with symmetric keys, as per the docs)
        symmetric_key = bytes(getrandbits(8) for _ in range(32))
        assert len(symmetric_key) == 32

        # import symmetric key (key material) into KMS
        public_key = load_der_public_key(params["PublicKey"])
        encrypted_key = public_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
            ),
        )
        describe_key_before_import = aws_client.kms.describe_key(KeyId=key_id)
        snapshot.match("describe-key-before-import", describe_key_before_import)

        with pytest.raises(ClientError) as e:
            aws_client.kms.import_key_material(
                KeyId=key_id,
                ImportToken=params["ImportToken"],
                EncryptedKeyMaterial=encrypted_key,
            )
        snapshot.match("import-expiring-key-without-valid-to", e.value.response)
        aws_client.kms.import_key_material(
            KeyId=key_id,
            ImportToken=params["ImportToken"],
            EncryptedKeyMaterial=encrypted_key,
            ExpirationModel="KEY_MATERIAL_DOES_NOT_EXPIRE",
        )
        describe_key_after_import = aws_client.kms.describe_key(KeyId=key_id)
        snapshot.match("describe-key-after-import", describe_key_after_import)

        # use key to encrypt/decrypt data
        encrypt_result = aws_client.kms.encrypt(Plaintext=plaintext, KeyId=key_id)
        api_decrypted = aws_client.kms.decrypt(
            CiphertextBlob=encrypt_result["CiphertextBlob"], KeyId=key_id
        )
        assert api_decrypted["Plaintext"] == plaintext

        aws_client.kms.delete_imported_key_material(KeyId=key_id)
        describe_key_after_deleted_import = aws_client.kms.describe_key(KeyId=key_id)
        snapshot.match("describe-key-after-deleted-import", describe_key_after_deleted_import)

        with pytest.raises(ClientError) as e:
            aws_client.kms.encrypt(Plaintext=plaintext, KeyId=key_id)
        snapshot.match("encrypt-after-delete-error", e.value.response)