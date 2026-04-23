async def performTokenRefresh(self, qwen_client: IQwenOAuth2Client, force_refresh: bool):
        lock_path = self.getLockFilePath()
        try:
            if self.memory_cache["credentials"] is None:
                self.reloadCredentialsFromFile()
            qwen_client.setCredentials(self.memory_cache["credentials"])
            current_credentials = qwen_client.getCredentials()
            if not current_credentials.get("refresh_token"):
                raise TokenManagerError(TokenError.NO_REFRESH_TOKEN, "No refresh token")
            await self.acquireLock(lock_path)

            self.checkAndReloadIfNeeded()

            if (
                not force_refresh
                and self.memory_cache["credentials"]
                and self.isTokenValid(self.memory_cache["credentials"])
            ):
                qwen_client.setCredentials(self.memory_cache["credentials"])
                return self.memory_cache["credentials"]

            response = await qwen_client.refreshAccessToken()
            if not response or isErrorResponse(response):
                raise TokenManagerError(TokenError.REFRESH_FAILED, str(response))
            token_data = response
            if "access_token" not in token_data:
                raise TokenManagerError(TokenError.REFRESH_FAILED, "No access_token returned")

            credentials = {
                "access_token": token_data["access_token"],
                "token_type": token_data["token_type"],
                "refresh_token": token_data.get("refresh_token", current_credentials.get("refresh_token")),
                "resource_url": token_data.get("resource_url"),
                "expiry_date": int(time.time() * 1000) + token_data.get("expires_in", 0) * 1000,
            }
            self.memory_cache["credentials"] = credentials
            qwen_client.setCredentials(credentials)

            await self.saveCredentialsToFile(credentials)
            return credentials
        except Exception as e:
            if isinstance(e, TokenManagerError):
                raise
            raise

        finally:
            await self.releaseLock(lock_path)