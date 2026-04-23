def _probe_connection(
        self,
        **kwargs: Any,
    ) -> None:
        merged_kwargs = {**self.shared_base_kwargs, **kwargs}
        # add special timeout to make sure that we don't hang indefinitely
        merged_kwargs["timeout"] = self.PROBE_TIMEOUT

        with self._credentials_provider:
            credentials, _ = self._renew_credentials()
            if self.scoped_token:
                # v2 endpoint doesn't always work with scoped tokens, use v1
                token = credentials["confluence_access_token"]
                probe_url = f"{self.base_url}/rest/api/space?limit=1"
                import requests

                logging.info(f"First and Last 5 of token: {token[:5]}...{token[-5:]}")

                try:
                    r = requests.get(
                        probe_url,
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
                    r.raise_for_status()
                except HTTPError as e:
                    if e.response.status_code == 403:
                        logging.warning(
                            "scoped token authenticated but not valid for probe endpoint (spaces)"
                        )
                    else:
                        if "WWW-Authenticate" in e.response.headers:
                            logging.warning(
                                f"WWW-Authenticate: {e.response.headers['WWW-Authenticate']}"
                            )
                            logging.warning(f"Full error: {e.response.text}")
                        raise e
                return

            # probe connection with direct client, no retries
            if "confluence_refresh_token" in credentials:
                logging.info("Probing Confluence with OAuth Access Token.")

                oauth2_dict: dict[str, Any] = OnyxConfluence._make_oauth2_dict(
                    credentials
                )
                url = (
                    f"https://api.atlassian.com/ex/confluence/{credentials['cloud_id']}"
                )
                confluence_client_with_minimal_retries = Confluence(
                    url=url, oauth2=oauth2_dict, **merged_kwargs
                )
            else:
                logging.info("Probing Confluence with Personal Access Token.")
                url = self._url
                if self._is_cloud:
                    logging.info("running with cloud client")
                    confluence_client_with_minimal_retries = Confluence(
                        url=url,
                        username=credentials["confluence_username"],
                        password=credentials["confluence_access_token"],
                        **merged_kwargs,
                    )
                else:
                    confluence_client_with_minimal_retries = Confluence(
                        url=url,
                        token=credentials["confluence_access_token"],
                        **merged_kwargs,
                    )

            # This call sometimes hangs indefinitely, so we run it in a timeout
            spaces = run_with_timeout(
                timeout=10,
                func=confluence_client_with_minimal_retries.get_all_spaces,
                limit=1,
            )

            # uncomment the following for testing
            # the following is an attempt to retrieve the user's timezone
            # Unfornately, all data is returned in UTC regardless of the user's time zone
            # even tho CQL parses incoming times based on the user's time zone
            # space_key = spaces["results"][0]["key"]
            # space_details = confluence_client_with_minimal_retries.cql(f"space.key={space_key}+AND+type=space")

            if not spaces:
                raise RuntimeError(
                    f"No spaces found at {url}! "
                    "Check your credentials and wiki_base and make sure "
                    "is_cloud is set correctly."
                )

            logging.info("Confluence probe succeeded.")