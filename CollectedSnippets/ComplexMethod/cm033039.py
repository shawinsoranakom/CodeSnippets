def load_credentials(self, credentials: dict[str, Any]) -> dict[str, Any] | None:
        """Instantiate the Jira client using either an API token or username/password."""
        jira_url_for_client = self.jira_base_url
        if self.scoped_token:
            if is_atlassian_cloud_url(self.jira_base_url):
                try:
                    jira_url_for_client = scoped_url(self.jira_base_url, "jira")
                except ValueError as exc:
                    raise ConnectorValidationError(str(exc)) from exc
            else:
                logger.warning("[Jira] Scoped token requested but Jira base URL does not appear to be an Atlassian Cloud domain; scoped token ignored.")

        user_email = credentials.get("jira_user_email") or credentials.get("username")
        api_token = credentials.get("jira_api_token") or credentials.get("token") or credentials.get("api_token")
        password = credentials.get("jira_password") or credentials.get("password")
        rest_api_version = credentials.get("rest_api_version")

        if not rest_api_version:
            rest_api_version = JIRA_CLOUD_API_VERSION if api_token else JIRA_SERVER_API_VERSION
        options: dict[str, Any] = {"rest_api_version": rest_api_version}

        try:
            if user_email and api_token:
                self.jira_client = JIRA(
                    server=jira_url_for_client,
                    basic_auth=(user_email, api_token),
                    options=options,
                )
            elif api_token:
                self.jira_client = JIRA(
                    server=jira_url_for_client,
                    token_auth=api_token,
                    options=options,
                )
            elif user_email and password:
                self.jira_client = JIRA(
                    server=jira_url_for_client,
                    basic_auth=(user_email, password),
                    options=options,
                )
            else:
                raise ConnectorMissingCredentialError("Jira credentials must include either an API token or username/password.")
        except Exception as exc:  # pragma: no cover - jira lib raises many types
            raise ConnectorMissingCredentialError(f"Jira: {exc}") from exc
        self._sync_timezone_from_server()
        return None