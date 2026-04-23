async def _request_tokens(
        self,
        params: dict[str, str],
        current_credentials: Optional[OAuth2Credentials] = None,
    ) -> OAuth2Credentials:
        # Determine if this is a refresh token request
        is_refresh = params.get("grant_type") == "refresh_token"

        # Build request body with appropriate grant_type
        request_body = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            **params,
        }

        # Set default grant_type if not provided
        if "grant_type" not in request_body:
            request_body["grant_type"] = "authorization_code"

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # For refresh token requests, support HTTP Basic Authentication as recommended
        if is_refresh:
            # Option 1: Use HTTP Basic Auth (preferred by Linear)
            client_credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(client_credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"

            # Remove client credentials from body when using Basic Auth
            request_body.pop("client_id", None)
            request_body.pop("client_secret", None)

        response = await Requests().post(
            self.token_url, data=request_body, headers=headers
        )

        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get("error", "Unknown error")
                error_description = error_data.get("error_description", "")
                if error_description:
                    error_message = f"{error_message}: {error_description}"
            except json.JSONDecodeError:
                error_message = response.text
            raise LinearAPIException(
                f"Failed to fetch Linear tokens ({response.status}): {error_message}",
                response.status,
            )

        token_data = response.json()

        # Extract token expiration if provided (for new refresh token implementation)
        now = int(time.time())
        expires_in = token_data.get("expires_in")
        access_token_expires_at = None
        if expires_in:
            access_token_expires_at = now + expires_in

        # Get username - preserve from current credentials if refreshing
        username = None
        if current_credentials and is_refresh:
            username = current_credentials.username
        elif "user" in token_data:
            username = token_data["user"].get("name", "Unknown User")
        else:
            # Fetch username using the access token
            username = await self._request_username(token_data["access_token"])

        new_credentials = OAuth2Credentials(
            provider=self.PROVIDER_NAME,
            title=current_credentials.title if current_credentials else None,
            username=username or "Unknown User",
            access_token=token_data["access_token"],
            scopes=(
                token_data["scope"].split(",")
                if "scope" in token_data
                else (current_credentials.scopes if current_credentials else [])
            ),
            refresh_token=token_data.get("refresh_token"),
            access_token_expires_at=access_token_expires_at,
            refresh_token_expires_at=None,  # Linear doesn't provide refresh token expiration
        )

        if current_credentials:
            new_credentials.id = current_credentials.id

        return new_credentials