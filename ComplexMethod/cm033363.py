def _validate_jwt_auth(security_cfg):
        """Validate JWT token in Authorization header."""
        jwt_cfg = security_cfg.get("jwt", {})
        secret = jwt_cfg.get("secret")
        if not secret:
            raise Exception("JWT secret not configured")

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise Exception("Missing Bearer token")

        token = auth_header[len("Bearer "):].strip()
        if not token:
            raise Exception("Empty Bearer token")

        alg = (jwt_cfg.get("algorithm") or "HS256").upper()

        decode_kwargs = {
            "key": secret,
            "algorithms": [alg],
        }
        options = {}
        if jwt_cfg.get("audience"):
            decode_kwargs["audience"] = jwt_cfg["audience"]
            options["verify_aud"] = True
        else:
            options["verify_aud"] = False

        if jwt_cfg.get("issuer"):
            decode_kwargs["issuer"] = jwt_cfg["issuer"]
            options["verify_iss"] = True
        else:
            options["verify_iss"] = False
        try:
            decoded = jwt.decode(
                token,
                options=options,
                **decode_kwargs,
            )
        except Exception as e:
            raise Exception(f"Invalid JWT: {str(e)}")

        raw_required_claims = jwt_cfg.get("required_claims", [])
        if isinstance(raw_required_claims, str):
            required_claims = [raw_required_claims]
        elif isinstance(raw_required_claims, (list, tuple, set)):
            required_claims = list(raw_required_claims)
        else:
            required_claims = []

        required_claims = [
            c for c in required_claims
            if isinstance(c, str) and c.strip()
        ]

        RESERVED_CLAIMS = {"exp", "sub", "aud", "iss", "nbf", "iat"}
        for claim in required_claims:
            if claim in RESERVED_CLAIMS:
                raise Exception(f"Reserved JWT claim cannot be required: {claim}")

        for claim in required_claims:
            if claim not in decoded:
                raise Exception(f"Missing JWT claim: {claim}")

        return decoded