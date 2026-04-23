def validate_connector_settings(self) -> None:
        """Validate connector settings"""
        if self.fast_client is None:
            raise ConnectorMissingCredentialError("Slack credentials not loaded.")

        try:
            # 1) Validate workspace connection
            auth_response = self.fast_client.auth_test()
            if not auth_response.get("ok", False):
                error_msg = auth_response.get(
                    "error", "Unknown error from Slack auth_test"
                )
                raise ConnectorValidationError(f"Failed Slack auth_test: {error_msg}")

            # 2) Confirm listing channels functionality works
            test_resp = self.fast_client.conversations_list(
                limit=1, types=["public_channel"]
            )
            if not test_resp.get("ok", False):
                error_msg = test_resp.get("error", "Unknown error from Slack")
                if error_msg == "invalid_auth":
                    raise ConnectorValidationError(
                        f"Invalid Slack bot token ({error_msg})."
                    )
                elif error_msg == "not_authed":
                    raise CredentialExpiredError(
                        f"Invalid or expired Slack bot token ({error_msg})."
                    )
                raise UnexpectedValidationError(
                    f"Slack API returned a failure: {error_msg}"
                )

        except SlackApiError as e:
            slack_error = e.response.get("error", "")
            if slack_error == "ratelimited":
                retry_after = int(e.response.headers.get("Retry-After", 1))
                logging.warning(
                    f"Slack API rate limited during validation. Retry suggested after {retry_after} seconds. "
                    "Proceeding with validation, but be aware that connector operations might be throttled."
                )
                return
            elif slack_error == "missing_scope":
                raise InsufficientPermissionsError(
                    "Slack bot token lacks the necessary scope to list/access channels. "
                    "Please ensure your Slack app has 'channels:read' (and/or 'groups:read' for private channels)."
                )
            elif slack_error == "invalid_auth":
                raise CredentialExpiredError(
                    f"Invalid Slack bot token ({slack_error})."
                )
            elif slack_error == "not_authed":
                raise CredentialExpiredError(
                    f"Invalid or expired Slack bot token ({slack_error})."
                )
            raise UnexpectedValidationError(
                f"Unexpected Slack error '{slack_error}' during settings validation."
            )
        except ConnectorValidationError as e:
            raise e
        except Exception as e:
            raise UnexpectedValidationError(
                f"Unexpected error during Slack settings validation: {e}"
            )