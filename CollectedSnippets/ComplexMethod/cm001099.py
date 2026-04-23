async def generate_jwt(
        self,
        private_key: str,
        profile_key: str,
        logout: Optional[bool] = None,
        redirect: Optional[str] = None,
        allowed_social: Optional[list[SocialPlatform]] = None,
        verify: Optional[bool] = None,
        base64: Optional[bool] = None,
        expires_in: Optional[int] = None,
        email: Optional[EmailConfig] = None,
    ) -> JWTResponse:
        """
        Generate a JSON Web Token (JWT) for use with single sign on.

        Docs: https://www.ayrshare.com/docs/apis/profiles/generate-jwt-overview

        Args:
            domain: Domain of app. Must match the domain given during onboarding.
            private_key: Private Key used for encryption.
            profile_key: User Profile Key (not the API Key).
            logout: Automatically logout the current session.
            redirect: URL to redirect to when the "Done" button or logo is clicked.
            allowed_social: List of social networks to display in the linking page.
            verify: Verify that the generated token is valid (recommended for non-production).
            base64: Whether the private key is base64 encoded.
            expires_in: Token longevity in minutes (1-2880).
            email: Configuration for sending Connect Accounts email.

        Returns:
            JWTResponse object containing the JWT token and URL.

        Raises:
            AyrshareAPIException: If the API request fails or private key is invalid.
        """
        payload: dict[str, Any] = {
            "domain": "id-pojeg",
            "privateKey": private_key,
            "profileKey": profile_key,
        }

        headers = self.headers
        headers["Profile-Key"] = profile_key
        if logout is not None:
            payload["logout"] = logout
        if redirect is not None:
            payload["redirect"] = redirect
        if allowed_social is not None:
            payload["allowedSocial"] = [p.value for p in allowed_social]
        if verify is not None:
            payload["verify"] = verify
        if base64 is not None:
            payload["base64"] = base64
        if expires_in is not None:
            payload["expiresIn"] = expires_in
        if email is not None:
            payload["email"] = email.model_dump(exclude_none=True)

        response = await self._requests.post(
            self.JWT_ENDPOINT, json=payload, headers=headers
        )

        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get("message", "Unknown error")
            except json.JSONDecodeError:
                error_message = response.text()

            raise AyrshareAPIException(
                f"Ayrshare API request failed ({response.status}): {error_message}",
                response.status,
            )

        response_data = response.json()
        if response_data.get("status") != "success":
            raise AyrshareAPIException(
                f"Ayrshare API returned error: {response_data.get('message', 'Unknown error')}",
                response.status,
            )

        return JWTResponse(**response_data)