def _validate_plaintext_key_type_based(
        self,
        plaintext: PlaintextType,
        key: KmsKey,
        encryption_algorithm: EncryptionAlgorithmSpec = None,
    ):
        # max size values extracted from AWS boto3 documentation
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms/client/encrypt.html
        max_size_bytes = 4096  # max allowed size
        if (
            key.metadata["KeySpec"] == KeySpec.RSA_2048
            and encryption_algorithm == EncryptionAlgorithmSpec.RSAES_OAEP_SHA_1
        ):
            max_size_bytes = 214
        elif (
            key.metadata["KeySpec"] == KeySpec.RSA_2048
            and encryption_algorithm == EncryptionAlgorithmSpec.RSAES_OAEP_SHA_256
        ):
            max_size_bytes = 190
        elif (
            key.metadata["KeySpec"] == KeySpec.RSA_3072
            and encryption_algorithm == EncryptionAlgorithmSpec.RSAES_OAEP_SHA_1
        ):
            max_size_bytes = 342
        elif (
            key.metadata["KeySpec"] == KeySpec.RSA_3072
            and encryption_algorithm == EncryptionAlgorithmSpec.RSAES_OAEP_SHA_256
        ):
            max_size_bytes = 318
        elif (
            key.metadata["KeySpec"] == KeySpec.RSA_4096
            and encryption_algorithm == EncryptionAlgorithmSpec.RSAES_OAEP_SHA_1
        ):
            max_size_bytes = 470
        elif (
            key.metadata["KeySpec"] == KeySpec.RSA_4096
            and encryption_algorithm == EncryptionAlgorithmSpec.RSAES_OAEP_SHA_256
        ):
            max_size_bytes = 446

        if len(plaintext) > max_size_bytes:
            raise ValidationException(
                f"Algorithm {encryption_algorithm} and key spec {key.metadata['KeySpec']} cannot encrypt data larger than {max_size_bytes} bytes."
            )