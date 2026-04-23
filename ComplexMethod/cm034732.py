async def initialize_auth(self) -> None:
        """
        Initialize authentication by using cached token, or refreshing if needed.
        Raises RuntimeError if no valid token can be obtained.
        """
        # Try cached token from KV store or in-memory cache
        cached = await self._get_cached_token()
        now = time.time()
        if cached:
            expires_at = cached["expiry_date"] / 1000  # ms to seconds
            if expires_at - now > self.TOKEN_BUFFER_TIME:
                self._access_token = cached["access_token"]
                self._expiry = expires_at
                return  # Use cached token if valid

        path = AuthManager.get_cache_file()
        if not path.exists():
            path = get_oauth_creds_path()
        if path.exists():
            try:
                with path.open("r") as f:
                    creds = json.load(f)
            except Exception as e:
                raise RuntimeError(f"Failed to read OAuth credentials from {path}: {e}")
        else:
            # Parse credentials from environment
            if "GCP_SERVICE_ACCOUNT" not in self.env:
                raise RuntimeError("GCP_SERVICE_ACCOUNT environment variable not set.")
            creds = json.loads(self.env["GCP_SERVICE_ACCOUNT"])

        refresh_token = creds.get("refresh_token")
        access_token = creds.get("access_token")
        expiry_date = creds.get("expiry_date")  # milliseconds since epoch

        # Use original access token if still valid
        if access_token and expiry_date:
            expires_at = expiry_date / 1000
            if expires_at - now > self.TOKEN_BUFFER_TIME:
                self._access_token = access_token
                self._expiry = expires_at
                await self._cache_token(access_token, expiry_date)
                return

        # Otherwise, refresh token
        if not refresh_token:
            raise RuntimeError("No refresh token found in GCP_SERVICE_ACCOUNT.")

        await self._refresh_and_cache_token(refresh_token)