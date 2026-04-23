def validate_connector_settings(self) -> None:
        """Validate WebDAV connector settings.

        Validation should exercise the same code-paths used by the connector
        (directory listing / PROPFIND), avoiding exists() which may probe with
        methods that differ across servers.
        """
        if self.client is None:
            raise ConnectorMissingCredentialError("WebDAV credentials not loaded.")

        if not self.base_url:
            raise ConnectorValidationError("No base URL was provided in connector settings.")

        # Normalize directory path: for collections, many servers behave better with trailing '/'
        test_path = self.remote_path or "/"
        if not test_path.startswith("/"):
            test_path = f"/{test_path}"
        if test_path != "/" and not test_path.endswith("/"):
            test_path = f"{test_path}/"

        try:
            # Use the same behavior as real sync: list directory with details (PROPFIND)
            self.client.ls(test_path, detail=True)

        except Exception as e:
            # Prefer structured status codes if present on the exception/response
            status = None
            for attr in ("status_code", "code"):
                v = getattr(e, attr, None)
                if isinstance(v, int):
                    status = v
                    break
            if status is None:
                resp = getattr(e, "response", None)
                v = getattr(resp, "status_code", None)
                if isinstance(v, int):
                    status = v

            # If we can classify by status code, do it
            if status == 401:
                raise CredentialExpiredError("WebDAV credentials appear invalid or expired.")
            if status == 403:
                raise InsufficientPermissionsError(
                    f"Insufficient permissions to access path '{self.remote_path}' on WebDAV server."
                )
            if status == 404:
                raise ConnectorValidationError(
                    f"Remote path '{self.remote_path}' does not exist on WebDAV server."
                )

            # Fallback: avoid brittle substring matching that caused false positives.
            # Provide the original exception for diagnosis.
            raise ConnectorValidationError(
                f"WebDAV validation failed for path '{test_path}': {repr(e)}"
            )