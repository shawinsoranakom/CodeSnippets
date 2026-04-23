def update(
        self,
        description: ConnectionDescription,
        authorization_type: ConnectionAuthorizationType,
        auth_parameters: UpdateConnectionAuthRequestParameters,
        invocation_connectivity_parameters: ConnectivityResourceParameters | None = None,
    ) -> None:
        self.set_state(ConnectionState.UPDATING)
        if description:
            self.connection.description = description
        if invocation_connectivity_parameters:
            self.connection.invocation_connectivity_parameters = invocation_connectivity_parameters
        # Use existing values if not provided in update
        if authorization_type:
            auth_type = (
                authorization_type.value
                if hasattr(authorization_type, "value")
                else authorization_type
            )
            self._validate_auth_type(auth_type)
        else:
            auth_type = self.connection.authorization_type

        try:
            if self.connection.secret_arn:
                self.update_connection_secret(
                    self.connection.secret_arn, auth_type, auth_parameters
                )
            else:
                secret_arn = self.create_connection_secret(
                    self.connection.region,
                    self.connection.account_id,
                    self.connection.name,
                    auth_type,
                    auth_parameters,
                )
                self.connection.secret_arn = secret_arn
                self.connection.last_authorized_time = datetime.now(UTC)

            # Set new values
            self.connection.authorization_type = auth_type
            public_auth_parameters = (
                self._get_public_parameters(authorization_type, auth_parameters)
                if auth_parameters
                else self.connection.auth_parameters
            )
            self.connection.auth_parameters = public_auth_parameters
            self.set_state(ConnectionState.AUTHORIZED)
            self.connection.last_modified_time = datetime.now(UTC)

        except Exception as error:
            LOG.warning(
                "Connection with name %s updating failed with errors: %s.",
                self.connection.name,
                error,
            )