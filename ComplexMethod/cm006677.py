def setup_rsa_keys(self):
        """Generate or load RSA keys when using RS256/RS512 algorithm."""
        if not self.ALGORITHM.is_asymmetric():
            return self

        config_dir = self.CONFIG_DIR
        private_key_value = self.PRIVATE_KEY.get_secret_value() if self.PRIVATE_KEY else ""

        if not config_dir:
            # No config dir - generate keys in memory if not provided
            if not private_key_value:
                logger.debug("No CONFIG_DIR provided, generating RSA keys in memory")
                private_key_pem, public_key_pem = generate_rsa_key_pair()
                object.__setattr__(self, "PRIVATE_KEY", SecretStr(private_key_pem))
                object.__setattr__(self, "PUBLIC_KEY", public_key_pem)
            elif not self.PUBLIC_KEY:
                # Derive public key from private key
                public_key_pem = derive_public_key_from_private(private_key_value)
                object.__setattr__(self, "PUBLIC_KEY", public_key_pem)
            return self

        private_key_path = Path(config_dir) / "private_key.pem"
        public_key_path = Path(config_dir) / "public_key.pem"

        if private_key_value:
            # Private key provided via env var - save it and derive public key
            logger.debug("RSA private key provided")
            write_secret_to_file(private_key_path, private_key_value)

            if not self.PUBLIC_KEY:
                public_key_pem = derive_public_key_from_private(private_key_value)
                object.__setattr__(self, "PUBLIC_KEY", public_key_pem)
                write_public_key_to_file(public_key_path, public_key_pem)
        # No private key provided - load from file or generate
        elif private_key_path.exists():
            logger.debug("Loading RSA keys from files")
            private_key_pem = read_secret_from_file(private_key_path)
            object.__setattr__(self, "PRIVATE_KEY", SecretStr(private_key_pem))

            if public_key_path.exists():
                public_key_pem = public_key_path.read_text(encoding="utf-8")
                object.__setattr__(self, "PUBLIC_KEY", public_key_pem)
            else:
                # Derive public key from private key
                public_key_pem = derive_public_key_from_private(private_key_pem)
                object.__setattr__(self, "PUBLIC_KEY", public_key_pem)
                write_public_key_to_file(public_key_path, public_key_pem)
        else:
            # Generate new RSA key pair
            logger.debug("Generating new RSA key pair")
            private_key_pem, public_key_pem = generate_rsa_key_pair()
            write_secret_to_file(private_key_path, private_key_pem)
            write_public_key_to_file(public_key_path, public_key_pem)
            object.__setattr__(self, "PRIVATE_KEY", SecretStr(private_key_pem))
            object.__setattr__(self, "PUBLIC_KEY", public_key_pem)
            logger.debug("RSA key pair generated and saved")

        return self