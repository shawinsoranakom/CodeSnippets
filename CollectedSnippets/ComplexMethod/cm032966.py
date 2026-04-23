def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        logger.debug("Loading credentials for SeaFile server %s", self.seafile_url)

        token = credentials.get("seafile_token")
        repo_token = credentials.get("repo_token")
        username = credentials.get("username")
        password = credentials.get("password")

        if token:
            self.token = token
        elif username and password:
            self.token = self._authenticate_with_password(username, password)

        if repo_token and self.sync_scope in (SeafileSyncScope.LIBRARY, SeafileSyncScope.DIRECTORY):
            self.repo_token = repo_token
        elif repo_token:
            logger.debug(
                "repo_token supplied but scope=%s; ignoring.",
                self.sync_scope.value,
            )

        if not self.token and not self.repo_token:
            raise ConnectorMissingCredentialError(
                "SeaFile requires 'seafile_token', 'repo_token', "
                "or 'username'/'password'."
            )

        try:
            self._validate_credentials()
        except ConnectorMissingCredentialError:
            raise
        except Exception as e:
            raise CredentialExpiredError(
                f"SeaFile credential validation failed: {e}"
            )

        return None