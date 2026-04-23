def test_cross_accounts_access(
        self, aws_client, secondary_aws_client, kms_create_key, user_arn
    ):
        # Create the keys in the primary AWS account. They will only be referred to by their ARNs hereon
        key_arn_1 = kms_create_key()["Arn"]
        key_arn_2 = kms_create_key(KeyUsage="SIGN_VERIFY", KeySpec="RSA_4096")["Arn"]
        key_arn_3 = kms_create_key(KeyUsage="GENERATE_VERIFY_MAC", KeySpec="HMAC_512")["Arn"]

        # Create client in secondary account and attempt to run operations with the above keys
        client = secondary_aws_client.kms

        # Cross-account access is supported for following operations in KMS:
        # - CreateGrant
        # - DescribeKey
        # - GetKeyRotationStatus
        # - GetPublicKey
        # - ListGrants
        # - RetireGrant
        # - RevokeGrant

        response = client.create_grant(
            KeyId=key_arn_1,
            GranteePrincipal=user_arn,
            Operations=["Decrypt", "Encrypt"],
        )
        grant_token = response["GrantToken"]

        response = client.create_grant(
            KeyId=key_arn_2,
            GranteePrincipal=user_arn,
            Operations=["Sign", "Verify"],
        )
        grant_id = response["GrantId"]

        assert client.describe_key(KeyId=key_arn_1)["KeyMetadata"]

        assert client.get_key_rotation_status(KeyId=key_arn_1)

        assert client.get_public_key(KeyId=key_arn_1)

        assert client.list_grants(KeyId=key_arn_1)["Grants"]

        assert client.retire_grant(GrantToken=grant_token)

        assert client.revoke_grant(GrantId=grant_id, KeyId=key_arn_2)

        # And additionally, the following cryptographic operations:
        # - Decrypt
        # - Encrypt
        # - GenerateDataKey
        # - GenerateDataKeyPair
        # - GenerateDataKeyPairWithoutPlaintext
        # - GenerateDataKeyWithoutPlaintext
        # - GenerateMac
        # - ReEncrypt
        # - Sign
        # - Verify
        # - VerifyMac

        assert client.generate_data_key(KeyId=key_arn_1)

        assert client.generate_data_key_without_plaintext(KeyId=key_arn_1)

        assert client.generate_data_key_pair(KeyId=key_arn_1, KeyPairSpec="RSA_2048")

        assert client.generate_data_key_pair_without_plaintext(
            KeyId=key_arn_1, KeyPairSpec="RSA_2048"
        )

        plaintext = "hello"
        ciphertext = client.encrypt(KeyId=key_arn_1, Plaintext="hello")["CiphertextBlob"]

        response = client.decrypt(CiphertextBlob=ciphertext, KeyId=key_arn_1)
        assert plaintext == to_str(response["Plaintext"])

        message = "world"
        signature = client.sign(
            KeyId=key_arn_2,
            MessageType="RAW",
            Message=message,
            SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256",
        )["Signature"]

        assert client.verify(
            KeyId=key_arn_2,
            Signature=signature,
            Message=message,
            SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256",
        )["SignatureValid"]

        mac = client.generate_mac(KeyId=key_arn_3, Message=message, MacAlgorithm="HMAC_SHA_512")[
            "Mac"
        ]

        assert client.verify_mac(
            KeyId=key_arn_3, Message=message, MacAlgorithm="HMAC_SHA_512", Mac=mac
        )["MacValid"]