def validate_connector_settings(self) -> None:
        if not self.token and not self.repo_token:
            raise ConnectorMissingCredentialError("SeaFile credentials not loaded.")
        if not self.seafile_url:
            raise ConnectorValidationError("No SeaFile URL was provided.")

        try:
            if self.sync_scope == SeafileSyncScope.ACCOUNT:
                libs = self._get_libraries()
                logger.info("Validated (account scope). %d libraries.", len(libs))
            elif self.sync_scope == SeafileSyncScope.LIBRARY:
                info = self._get_repo_info()
                logger.info(
                    "Validated (library scope): %s", info.get("name", self.repo_id)
                )
            elif self.sync_scope == SeafileSyncScope.DIRECTORY:
                entries = self._get_directory_entries(self.repo_id, self.sync_path)
                logger.info(
                    "Validated (directory scope): %s:%s (%d entries)",
                    self.repo_id, self.sync_path, len(entries),
                )
        except (
            ConnectorValidationError, ConnectorMissingCredentialError,
            CredentialExpiredError, InsufficientPermissionsError,
        ):
            raise
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status == 401:
                raise CredentialExpiredError("Token invalid or expired.")
            if status == 403:
                raise InsufficientPermissionsError("Insufficient permissions.")
            raise ConnectorValidationError(f"Validation failed: {repr(e)}")