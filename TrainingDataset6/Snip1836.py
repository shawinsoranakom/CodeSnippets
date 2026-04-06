def make_not_authenticated_error(self) -> HTTPException:
        """
        The OAuth 2 specification doesn't define the challenge that should be used,
        because a `Bearer` token is not really the only option to authenticate.

        But declaring any other authentication challenge would be application-specific
        as it's not defined in the specification.

        For practical reasons, this method uses the `Bearer` challenge by default, as
        it's probably the most common one.

        If you are implementing an OAuth2 authentication scheme other than the provided
        ones in FastAPI (based on bearer tokens), you might want to override this.

        Ref: https://datatracker.ietf.org/doc/html/rfc6749
        """
        return HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )