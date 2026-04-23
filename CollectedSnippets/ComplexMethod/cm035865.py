async def authorize_user(
        self, user_info: KeycloakUserInfo
    ) -> UserAuthorizationResponse:
        user_id = user_info.sub
        email = user_info.email
        provider_type = user_info.identity_provider
        try:
            if not email:
                logger.warning(f'No email provided for user_id: {user_id}')
                return UserAuthorizationResponse(
                    success=False, error_detail='missing_email'
                )

            if self.prevent_duplicates:
                has_duplicate = await token_manager.check_duplicate_base_email(
                    email, user_id
                )
                if has_duplicate:
                    logger.warning(
                        f'Blocked signup attempt for email {email} - duplicate base email found',
                        extra={'user_id': user_id, 'email': email},
                    )
                    return UserAuthorizationResponse(
                        success=False, error_detail='duplicate_email'
                    )

            # Check authorization rules (whitelist takes precedence over blacklist)
            base_email = extract_base_email(email)
            if base_email is None:
                return UserAuthorizationResponse(
                    success=False, error_detail='invalid_email'
                )
            auth_type = await UserAuthorizationStore.get_authorization_type(
                base_email, provider_type
            )

            if auth_type == UserAuthorizationType.WHITELIST:
                logger.debug(
                    f'User {email} matched whitelist rule',
                    extra={'user_id': user_id, 'email': email},
                )
                return UserAuthorizationResponse(success=True)

            if auth_type == UserAuthorizationType.BLACKLIST:
                logger.warning(
                    f'Blocked authentication attempt for email: {email}, user_id: {user_id}'
                )
                return UserAuthorizationResponse(success=False, error_detail='blocked')

            return UserAuthorizationResponse(success=True)
        except Exception:
            logger.exception('error authorizing user', extra={'user_id': user_id})
            return UserAuthorizationResponse(success=False)