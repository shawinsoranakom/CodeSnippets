def validate_connector_settings(self) -> None:
        """Validate Dropbox connector settings"""
        if self.dropbox_client is None:
            raise ConnectorMissingCredentialError("Dropbox")

        try:
            self.dropbox_client.files_list_folder(path="", limit=1)
        except AuthError as e:
            logger.exception("[Dropbox]: Failed to validate Dropbox credentials")
            raise ConnectorValidationError(f"Dropbox credential is invalid: {e}")
        except ApiError as e:
            if e.error is not None and "insufficient_permissions" in str(e.error).lower():
                raise InsufficientPermissionsError("Your Dropbox token does not have sufficient permissions.")
            raise ConnectorValidationError(f"Unexpected Dropbox error during validation: {e.user_message_text or e}")
        except Exception as e:
            raise ConnectorValidationError(f"Unexpected error during Dropbox settings validation: {e}")