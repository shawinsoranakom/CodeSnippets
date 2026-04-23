def _renew_credentials(self) -> tuple[dict[str, Any], bool]:
        """credential_json - the current json credentials
        Returns a tuple
        1. The up-to-date credentials
        2. True if the credentials were updated

        This method is intended to be used within a distributed lock.
        Lock, call this, update credentials if the tokens were refreshed, then release
        """
        # static credentials are preloaded, so no locking/redis required
        if self.static_credentials:
            return self.static_credentials, False

        if not self.redis_client:
            raise RuntimeError("self.redis_client is None")

        # dynamic credentials need locking
        # check redis first, then fallback to the DB
        credential_raw = self.redis_client.get(self.credential_key)
        if credential_raw is not None:
            credential_bytes = cast(bytes, credential_raw)
            credential_str = credential_bytes.decode("utf-8")
            credential_json: dict[str, Any] = json.loads(credential_str)
        else:
            credential_json = self._credentials_provider.get_credentials()

        if "confluence_refresh_token" not in credential_json:
            # static credentials ... cache them permanently and return
            self.static_credentials = credential_json
            return credential_json, False

        if not OAUTH_CONFLUENCE_CLOUD_CLIENT_ID:
            raise RuntimeError("OAUTH_CONFLUENCE_CLOUD_CLIENT_ID must be set!")

        if not OAUTH_CONFLUENCE_CLOUD_CLIENT_SECRET:
            raise RuntimeError("OAUTH_CONFLUENCE_CLOUD_CLIENT_SECRET must be set!")

        # check if we should refresh tokens. we're deciding to refresh halfway
        # to expiration
        now = datetime.now(timezone.utc)
        created_at = datetime.fromisoformat(credential_json["created_at"])
        expires_in: int = credential_json["expires_in"]
        renew_at = created_at + timedelta(seconds=expires_in // 2)
        if now <= renew_at:
            # cached/current credentials are reasonably up to date
            return credential_json, False

        # we need to refresh
        logging.info("Renewing Confluence Cloud credentials...")
        new_credentials = confluence_refresh_tokens(
            OAUTH_CONFLUENCE_CLOUD_CLIENT_ID,
            OAUTH_CONFLUENCE_CLOUD_CLIENT_SECRET,
            credential_json["cloud_id"],
            credential_json["confluence_refresh_token"],
        )

        # store the new credentials to redis and to the db through the provider
        # redis: we use a 5 min TTL because we are given a 10 minutes grace period
        # when keys are rotated. it's easier to expire the cached credentials
        # reasonably frequently rather than trying to handle strong synchronization
        # between the db and redis everywhere the credentials might be updated
        new_credential_str = json.dumps(new_credentials)
        self.redis_client.set(
            self.credential_key, new_credential_str, exp=self.CREDENTIAL_TTL
        )
        self._credentials_provider.set_credentials(new_credentials)

        return new_credentials, True