async def process_callback(self, code: str, state: str | None = None) -> User:
        """Exchange code for access token and get user info."""
        if not code:
            raise ProviderAuthException("github", "Authorization code is missing")

        # Exchange code for access token
        token_url = "https://github.com/login/oauth/access_token"
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.callback_url,
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data, headers={"Accept": "application/json"})

            if token_response.status_code != 200:
                logger.error(f"GitHub token exchange failed: {token_response.text}")
                raise ProviderAuthException("github", "Failed to exchange code for access token")

            token_json = token_response.json()
            access_token = token_json.get("access_token")

            if not access_token:
                logger.error(f"No access token in GitHub response: {token_json}")
                raise ProviderAuthException("github", "No access token received")

            # Get user info with the access token
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}", "Accept": "application/json"},
            )

            if user_response.status_code != 200:
                logger.error(f"GitHub user info fetch failed: {user_response.text}")
                raise ProviderAuthException("github", "Failed to fetch user information")

            user_data = user_response.json()

            # Get user emails if scope includes email
            email = None
            if "user:email" in self.scopes:
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"token {access_token}", "Accept": "application/json"},
                )

                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_emails = [e for e in emails if e.get("primary") is True]
                    if primary_emails:
                        email = primary_emails[0].get("email")

            # Create User object
            return User(
                id=str(user_data.get("id")),
                name=user_data.get("name") or user_data.get("login"),
                email=email,
                avatar_url=user_data.get("avatar_url"),
                provider="github",
                metadata={
                    "login": user_data.get("login"),
                    "github_id": user_data.get("id"),
                    "access_token": access_token,
                },
            )