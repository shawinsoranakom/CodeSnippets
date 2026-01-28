def validate(self):
        if not self.JWT_VERIFY_KEY:
            raise AuthConfigError(
                "JWT_VERIFY_KEY must be set. "
                "An empty JWT secret would allow anyone to forge valid tokens."
            )

        if len(self.JWT_VERIFY_KEY) < 32:
            logger.warning(
                "⚠️ JWT_VERIFY_KEY appears weak (less than 32 characters). "
                "Consider using a longer, cryptographically secure secret."
            )

        supported_algorithms = get_default_algorithms().keys()

        if not has_crypto:
            logger.warning(
                "⚠️ Asymmetric JWT verification is not available "
                "because the 'cryptography' package is not installed. "
                + ALGO_RECOMMENDATION
            )

        if (
            self.JWT_ALGORITHM not in supported_algorithms
            or self.JWT_ALGORITHM == "none"
        ):
            raise AuthConfigError(
                f"Invalid JWT_SIGN_ALGORITHM: '{self.JWT_ALGORITHM}'. "
                "Supported algorithms are listed on "
                "https://pyjwt.readthedocs.io/en/stable/algorithms.html"
            )

        if self.JWT_ALGORITHM.startswith("HS"):
            logger.warning(
                f"⚠️ JWT_SIGN_ALGORITHM is set to '{self.JWT_ALGORITHM}', "
                "a symmetric shared-key signature algorithm. " + ALGO_RECOMMENDATION
            )
