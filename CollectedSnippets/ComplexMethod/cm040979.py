def assert_valid(key_spec: str):
        """
        Validates that the given ``key_spec`` is supported in the current context.

        :param key_spec: The key specification to validate.
        :type key_spec: str
        :raises ValidationException: If ``key_spec`` is not a known valid spec.
        :raises UnsupportedOperationException: If ``key_spec`` is entirely unsupported.
        """

        def raise_validation():
            raise ValidationException(
                f"1 validation error detected: Value '{key_spec}' at 'keySpec' "
                f"failed to satisfy constraint: Member must satisfy enum value set: "
                f"[RSA_2048, ECC_NIST_P384, ECC_NIST_P256, ECC_NIST_P521, HMAC_384, RSA_3072, "
                f"ECC_SECG_P256K1, RSA_4096, SYMMETRIC_DEFAULT, HMAC_256, HMAC_224, HMAC_512]"
            )

        if key_spec == "SYMMETRIC_DEFAULT":
            return

        if key_spec.startswith("RSA"):
            if key_spec not in RSA_CRYPTO_KEY_LENGTHS:
                raise_validation()
            return

        if key_spec.startswith("ECC"):
            if key_spec not in ECC_CURVES:
                raise_validation()
            return

        if key_spec.startswith("HMAC"):
            if key_spec not in HMAC_RANGE_KEY_LENGTHS:
                raise_validation()
            return

        raise UnsupportedOperationException(f"KeySpec {key_spec} is not supported")