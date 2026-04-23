def validate_connector_settings(self) -> None:
        """Validate Notion connector settings and credentials."""
        if not self.headers.get("Authorization"):
            raise ConnectorMissingCredentialError("Notion credentials not loaded.")

        try:
            if self.root_page_id:
                response = rl_requests.get(
                    f"https://api.notion.com/v1/pages/{self.root_page_id}",
                    headers=self.headers,
                    timeout=30,
                )
            else:
                test_query = {"filter": {"property": "object", "value": "page"}, "page_size": 1}
                response = rl_requests.post(
                    "https://api.notion.com/v1/search",
                    headers=self.headers,
                    json=test_query,
                    timeout=30,
                )

            response.raise_for_status()

        except rl_requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else None

            if status_code == 401:
                raise CredentialExpiredError("Notion credential appears to be invalid or expired (HTTP 401).")
            elif status_code == 403:
                raise InsufficientPermissionsError("Your Notion token does not have sufficient permissions (HTTP 403).")
            elif status_code == 404:
                raise ConnectorValidationError("Notion resource not found or not shared with the integration (HTTP 404).")
            elif status_code == 429:
                raise ConnectorValidationError("Validation failed due to Notion rate-limits being exceeded (HTTP 429).")
            else:
                raise UnexpectedValidationError(f"Unexpected Notion HTTP error (status={status_code}): {http_err}")

        except Exception as exc:
            raise UnexpectedValidationError(f"Unexpected error during Notion settings validation: {exc}")