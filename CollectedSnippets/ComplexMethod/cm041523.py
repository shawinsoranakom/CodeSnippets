def test_rotate_key_on_demand_updates_current_key_material_for_external_keys(
        self, kms_create_key, aws_client, snapshot
    ):
        snapshot.add_transformer(
            snapshot.transform.key_value("ImportToken", reference_replacement=False)
        )
        snapshot.add_transformer(
            snapshot.transform.key_value("PublicKey", reference_replacement=False)
        )

        create_key_response = kms_create_key(
            Origin="EXTERNAL", KeyUsage="ENCRYPT_DECRYPT", Description="test-key"
        )
        key_id = create_key_response["KeyId"]
        snapshot.match("create-kms-external-key", create_key_response)

        # Get the parameters required to import key material into our KMS key.
        get_parameters_response = aws_client.kms.get_parameters_for_import(
            KeyId=key_id, WrappingAlgorithm="RSAES_OAEP_SHA_256", WrappingKeySpec="RSA_2048"
        )
        assert get_parameters_response["KeyId"] == create_key_response["Arn"]
        assert get_parameters_response["ImportToken"]
        assert get_parameters_response["PublicKey"]
        assert isinstance(get_parameters_response["ParametersValidTo"], datetime)
        snapshot.match("get-import-parameters-response", get_parameters_response)

        # Create initial key material to use in external KMS key.
        initial_key_material = generate_encrypted_symmetric_key_material(
            get_parameters_response["PublicKey"]
        )
        describe_empty_key_response = aws_client.kms.describe_key(KeyId=key_id)
        snapshot.match("describe-empty-key-response", describe_empty_key_response)

        # Import the initial key material.
        import_key_material_response = aws_client.kms.import_key_material(
            KeyId=key_id,
            ImportToken=get_parameters_response["ImportToken"],
            EncryptedKeyMaterial=initial_key_material,
            ExpirationModel="KEY_MATERIAL_DOES_NOT_EXPIRE",
        )
        snapshot.match("import-key-material-response", import_key_material_response)

        # On initial import of material, it should automatically update the CurrentKeyMaterialId
        describe_key_with_material_response = aws_client.kms.describe_key(KeyId=key_id)
        assert "CurrentKeyMaterialId" in describe_key_with_material_response["KeyMetadata"]
        current_key_material_id = describe_key_with_material_response["KeyMetadata"][
            "CurrentKeyMaterialId"
        ]
        snapshot.match("describe-key-with-material-response", describe_key_with_material_response)

        # Encrypt/Decrypt using key material.
        plaintext = b"Hello World!1/?"
        encrypted_response = aws_client.kms.encrypt(
            Plaintext=plaintext, KeyId=key_id, EncryptionAlgorithm="SYMMETRIC_DEFAULT"
        )
        snapshot.match("kms-encrypt-initial-response", encrypted_response)
        initial_ciphertext = encrypted_response["CiphertextBlob"]

        decrypted_response = aws_client.kms.decrypt(
            CiphertextBlob=initial_ciphertext,
            KeyId=key_id,
        )
        assert decrypted_response["Plaintext"] == plaintext

        # Import new key material and ensure that the key uses the new material after on-demand rotation.
        new_get_parameters_response = aws_client.kms.get_parameters_for_import(
            KeyId=key_id, WrappingAlgorithm="RSAES_OAEP_SHA_256", WrappingKeySpec="RSA_2048"
        )
        new_key_material = generate_encrypted_symmetric_key_material(
            new_get_parameters_response["PublicKey"]
        )
        import_new_key_material_response = aws_client.kms.import_key_material(
            KeyId=key_id,
            ImportToken=new_get_parameters_response["ImportToken"],
            EncryptedKeyMaterial=new_key_material,
            ExpirationModel="KEY_MATERIAL_DOES_NOT_EXPIRE",
            ImportType="NEW_KEY_MATERIAL",  # Defaults to this if the key is empty, but will default to EXISTING_KEY_MATERIAL afterwards.
        )

        snapshot.match("import-new-key-material-response", import_new_key_material_response)
        describe_key_with_material_response = aws_client.kms.describe_key(KeyId=key_id)
        snapshot.match(
            "describe-key-with-new-material-response", describe_key_with_material_response
        )

        # Rotate to the new key material.
        rotate_on_demand_response = aws_client.kms.rotate_key_on_demand(KeyId=key_id)
        snapshot.match("rotate-key-on-demand-response", rotate_on_demand_response)

        def _assert_on_demand_rotation_updates_material():
            response = aws_client.kms.describe_key(KeyId=key_id)
            return response["KeyMetadata"]["CurrentKeyMaterialId"] != current_key_material_id

        assert poll_condition(
            condition=_assert_on_demand_rotation_updates_material,
            timeout=90,
            interval=5 if is_aws_cloud() else 0.5,
        )

        describe_key_after_rotate_response = aws_client.kms.describe_key(KeyId=key_id)
        snapshot.match("describe-key-after-rotation", describe_key_after_rotate_response)

        # Encrypt/Decrypt using the new key material.
        new_encrypted_response = aws_client.kms.encrypt(
            Plaintext=plaintext, KeyId=key_id, EncryptionAlgorithm="SYMMETRIC_DEFAULT"
        )
        snapshot.match("kms-encrypt-rotated-key-response", new_encrypted_response)
        new_ciphertext = new_encrypted_response["CiphertextBlob"]

        assert new_ciphertext != initial_ciphertext
        new_decrypted_response = aws_client.kms.decrypt(
            CiphertextBlob=new_ciphertext,
            KeyId=key_id,
            EncryptionAlgorithm="SYMMETRIC_DEFAULT",
        )
        assert new_decrypted_response["Plaintext"] == plaintext