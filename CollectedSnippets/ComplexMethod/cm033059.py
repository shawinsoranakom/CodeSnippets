def validate_connector_settings(self) -> None:
        if self._creds is None:
            raise ConnectorMissingCredentialError("Google Drive credentials not loaded.")

        if self._primary_admin_email is None:
            raise ConnectorValidationError("Primary admin email not found in credentials. Ensure DB_CREDENTIALS_PRIMARY_ADMIN_KEY is set.")

        try:
            drive_service = get_drive_service(self._creds, self._primary_admin_email)
            drive_service.files().list(pageSize=1, fields="files(id)").execute()

            if isinstance(self._creds, ServiceAccountCredentials):
                # default is ~17mins of retries, don't do that here since this is called from
                # the UI
                get_root_folder_id(drive_service)

        except HttpError as e:
            status_code = e.resp.status if e.resp else None
            if status_code == 401:
                raise CredentialExpiredError("Invalid or expired Google Drive credentials (401).")
            elif status_code == 403:
                raise InsufficientPermissionsError("Google Drive app lacks required permissions (403). Please ensure the necessary scopes are granted and Drive apps are enabled.")
            else:
                raise ConnectorValidationError(f"Unexpected Google Drive error (status={status_code}): {e}")

        except Exception as e:
            # Check for scope-related hints from the error message
            if MISSING_SCOPES_ERROR_STR in str(e):
                raise InsufficientPermissionsError("Google Drive credentials are missing required scopes.")
            raise ConnectorValidationError(f"Unexpected error during Google Drive validation: {e}")