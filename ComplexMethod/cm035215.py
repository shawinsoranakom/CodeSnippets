def decrypt_jwe_token(
        self, token: str, key_id: str | None = None
    ) -> dict[str, Any]:
        """Decrypt and decode a JWE token.

        Args:
            token: The JWE token to decrypt
            key_id: The key ID to use for decryption. If None, extracts
                    from token header.

        Returns:
            The decrypted JWT payload

        Raises:
            ValueError: If token is invalid or key_id is not found
            Exception: If token decryption fails
        """
        # Deserialize once and reuse for both header extraction and decryption
        try:
            jwe_obj = jwcrypto_jwe.JWE()
            jwe_obj.deserialize(token)
        except Exception:
            raise ValueError('Invalid JWE token format')

        # Extract and validate the protected header
        try:
            protected_header = json.loads(jwe_obj.objects['protected'])
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f'Invalid JWE token format: {type(e).__name__}')

        # Verify algorithms to prevent cryptographic agility attacks
        if (
            protected_header.get('alg') != 'dir'
            or protected_header.get('enc') != 'A256GCM'
        ):
            raise ValueError('Unsupported or unexpected JWE algorithm')

        if key_id is None:
            # Extract key_id from the token's header
            key_id = protected_header.get('kid')
            if not key_id:
                raise ValueError("Token does not contain 'kid' header with key ID")

        if key_id not in self._keys:
            raise ValueError(f"Key ID '{key_id}' not found")

        # Get the raw key for JWE decryption and derive a 256-bit key
        secret_key = self._keys[key_id].key.get_secret_value()
        key_bytes = secret_key.encode() if isinstance(secret_key, str) else secret_key
        # Derive a 256-bit key using SHA256
        key_256 = hashlib.sha256(key_bytes).digest()

        try:
            # Create JWK from symmetric key for jwcrypto
            symmetric_key = jwk.JWK(kty='oct', k=jwk.base64url_encode(key_256))

            # Decrypt the JWE token (reusing already deserialized jwe_obj)
            jwe_obj.decrypt(symmetric_key)

            # Parse the JSON string back to dictionary
            payload = json.loads(jwe_obj.payload.decode('utf-8'))
            return payload
        except Exception as e:
            raise Exception(f'Token decryption failed: {str(e)}')