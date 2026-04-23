async def authorize(self, request: Request) -> bool:
        """Authorize the request."""
        if not self.server_auth:
            return True

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme.")

            try:
                decoded = base64.b64decode(token).decode("utf-8")
                username, password = decoded.split(":", 1)
            except (binascii.Error, ValueError) as e:
                raise ValueError("Invalid base64-encoded token.") from e

            expected_username, expected_password = self.server_auth

            is_user_valid = secrets.compare_digest(username, expected_username)
            is_pass_valid = secrets.compare_digest(password, expected_password)

            if not (is_user_valid and is_pass_valid):
                raise ValueError("Invalid username or password.")

            request.state.user = {"username": username}
        except (ValueError, HTTPException) as e:
            detail = getattr(e, "detail", str(e))
            raise HTTPException(
                status_code=401,
                detail=detail,
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

        return True