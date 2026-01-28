def verify_key(
        self, provided_key: str, known_hash: str, known_salt: str | None = None
    ) -> bool:
        """
        Verify an API key against a known hash (+ salt).
        Supports verifying both legacy SHA256 and secure Scrypt hashes.
        """
        if not provided_key.startswith(self.PREFIX):
            return False

        # Handle legacy SHA256 hashes (migration support)
        if known_salt is None:
            legacy_hash = hashlib.sha256(provided_key.encode()).hexdigest()
            return secrets.compare_digest(legacy_hash, known_hash)

        try:
            salt_bytes = bytes.fromhex(known_salt)
            provided_hash = self._hash_key_with_salt(provided_key, salt_bytes)
            return secrets.compare_digest(provided_hash, known_hash)
        except (ValueError, TypeError):
            return False
