def _check_tos(self, request: Request):
        keycloak_auth_cookie = request.cookies.get('keycloak_auth')
        auth_header = request.headers.get('Authorization')
        mcp_auth_header = request.headers.get('X-Session-API-Key')
        api_auth_header = request.headers.get('X-Access-Token')
        accepted_tos: bool | None = False
        if (
            keycloak_auth_cookie is None
            and (auth_header is None or not auth_header.startswith('Bearer '))
            and mcp_auth_header is None
            and api_auth_header is None
        ):
            raise NoCredentialsError

        jwt_secret: SecretStr = config.jwt_secret  # type: ignore[assignment]
        if keycloak_auth_cookie:
            try:
                decoded = jwt.decode(
                    keycloak_auth_cookie,
                    jwt_secret.get_secret_value(),
                    algorithms=['HS256'],
                )
                accepted_tos = decoded.get('accepted_tos')
            except jwt.exceptions.InvalidSignatureError:
                # If we can't decode the token, treat it as an auth error
                logger.warning('Invalid JWT signature detected')
                raise AuthError('Invalid authentication token')
            except Exception as e:
                # Handle any other JWT decoding errors
                logger.warning(f'JWT decode error: {str(e)}')
                raise AuthError('Invalid authentication token')
        else:
            # Don't fail an API call if the TOS has not been accepted.
            # The user will accept the TOS the next time they login.
            accepted_tos = True

        # TODO: This explicitly checks for "False" so it doesn't logout anyone
        # that has logged in prior to this change:
        # accepted_tos is "None" means the user has not re-logged in since this TOS change.
        # accepted_tos is "False" means the user was shown the TOS but has not accepted.
        # accepted_tos is "True" means the user has accepted the TOS
        #
        # Once the initial deploy is complete and every user has been logged out
        # after this change (12 hrs max), this should be changed to check
        # "if accepted_tos is not None" as there should not be any users with
        # accepted_tos equal to "None"
        if accepted_tos is False and request.url.path != '/api/accept_tos':
            logger.warning('User has not accepted the terms of service')
            raise TosNotAcceptedError