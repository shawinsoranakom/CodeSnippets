def __init__(self, key_spec: str, key_material: bytes | None = None):
        self.private_key = None
        self.public_key = None
        self.pending_key_material = None
        # Technically, key_material, being a symmetric encryption key, is only relevant for
        #   key_spec == SYMMETRIC_DEFAULT.
        # But LocalStack uses symmetric encryption with this key_material even for other specs. Asymmetric keys are
        # generated, but are not actually used for encryption. Signing is different.
        self.key_material = key_material or os.urandom(SYMMETRIC_DEFAULT_MATERIAL_LENGTH)
        self.key_spec = key_spec

        KmsCryptoKey.assert_valid(key_spec)

        if key_spec == "SYMMETRIC_DEFAULT":
            return

        if key_spec.startswith("RSA"):
            key_size = RSA_CRYPTO_KEY_LENGTHS.get(key_spec)
            if key_material:
                key = crypto_serialization.load_der_private_key(key_material, password=None)
            else:
                key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        elif key_spec.startswith("ECC"):
            curve = ECC_CURVES.get(key_spec)
            if key_material:
                key = crypto_serialization.load_der_private_key(key_material, password=None)
            else:
                key = ec.generate_private_key(curve)
        elif key_spec.startswith("HMAC"):
            minimum_length, maximum_length = HMAC_RANGE_KEY_LENGTHS.get(key_spec)
            self.key_material = key_material or os.urandom(
                random.randint(minimum_length, maximum_length)
            )
            return

        self._serialize_key(key)