async def authenticate_request(self, request: Request) -> User:
        """Authenticate a request and return user information."""
        # Check if path should be excluded from auth
        # print("************ authenticating request ************", request.url.path, self.config.type )
        if request.url.path in self.config.exclude_paths:
            return User(id="guestuser@gmail.com", name="Default User", provider="none")

        if self.config.type == "none":
            # No auth mode - return default user
            return User(id="guestuser@gmail.com", name="Default User", provider="none")

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise MissingTokenException()

        token = auth_header.replace("Bearer ", "")

        try:
            if not self.config.jwt_secret:
                # For development with no JWT secret
                logger.warning("JWT secret not configured, accepting all tokens")
                return User(id="guestuser@gmail.com", name="Default User", provider="none")

            # Decode and validate JWT
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=["HS256"])

            # Create User object from token payload
            return User(
                id=payload.get("sub"),
                name=payload.get("name", "Unknown User"),
                email=payload.get("email"),
                provider=payload.get("provider", "jwt"),
                roles=payload.get("roles", ["user"]),
            )

        except jwt.ExpiredSignatureError as e:
            logger.warning(f"Expired token received: {token[:10]}...")
            raise InvalidTokenException() from e
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token received: {token[:10]}...")
            raise InvalidTokenException() from e