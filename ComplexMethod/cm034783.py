async def getValidCredentials(self, github_client, force_refresh: bool = False):
        try:
            self.checkAndReloadIfNeeded()

            if (
                self.memory_cache["credentials"]
                and not force_refresh
                and self.isTokenValid(self.memory_cache["credentials"])
            ):
                return self.memory_cache["credentials"]

            if self.refresh_promise:
                return await self.refresh_promise

            # Try to reload credentials from file
            try:
                self.reloadCredentialsFromFile()
                if self.memory_cache["credentials"] and self.isTokenValid(self.memory_cache["credentials"]):
                    return self.memory_cache["credentials"]
            except TokenManagerError:
                pass

            raise TokenManagerError(
                TokenError.FILE_ACCESS_ERROR,
                "No valid credentials found. Please run login first."
            )
        except Exception as e:
            if isinstance(e, TokenManagerError):
                raise
            raise TokenManagerError(TokenError.FILE_ACCESS_ERROR, str(e), e) from e