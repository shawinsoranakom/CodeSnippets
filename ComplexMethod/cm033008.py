def validate_connector_settings(self) -> None:
        try:
            spaces = self.low_timeout_confluence_client.get_all_spaces(limit=1)
        except HTTPError as e:
            status_code = e.response.status_code if e.response else None
            if status_code == 401:
                raise CredentialExpiredError(
                    "Invalid or expired Confluence credentials (HTTP 401)."
                )
            elif status_code == 403:
                raise InsufficientPermissionsError(
                    "Insufficient permissions to access Confluence resources (HTTP 403)."
                )
            raise UnexpectedValidationError(
                f"Unexpected Confluence error (status={status_code}): {e}"
            )
        except Exception as e:
            raise UnexpectedValidationError(
                f"Unexpected error while validating Confluence settings: {e}"
            )

        if self.space:
            try:
                self.low_timeout_confluence_client.get_space(self.space)
            except ApiError as e:
                raise ConnectorValidationError(
                    "Invalid Confluence space key provided"
                ) from e

        if not spaces or not spaces.get("results"):
            raise ConnectorValidationError(
                "No Confluence spaces found. Either your credentials lack permissions, or "
                "there truly are no spaces in this Confluence instance."
            )