async def device_token(device_code: str = Form(...)):
    """Poll for a token until the user authorizes or the code expires."""
    try:
        device_code_entry = await device_code_store.get_by_device_code(device_code)

        if not device_code_entry:
            return _oauth_error(
                status.HTTP_400_BAD_REQUEST,
                'invalid_grant',
                'Invalid device code',
            )

        # Check rate limiting (RFC 8628 section 3.5)
        is_too_fast, current_interval = device_code_entry.check_rate_limit()
        if is_too_fast:
            # Update poll time and increase interval
            await device_code_store.update_poll_time(
                device_code, increase_interval=True
            )
            logger.warning(
                'Client polling too fast, returning slow_down error',
                extra={
                    'device_code': device_code[:8] + '...',  # Log partial for privacy
                    'new_interval': current_interval,
                },
            )
            return _oauth_error(
                status.HTTP_400_BAD_REQUEST,
                'slow_down',
                f'Polling too frequently. Wait at least {current_interval} seconds between requests.',
                interval=current_interval,
            )

        # Update poll time for successful rate limit check
        await device_code_store.update_poll_time(device_code, increase_interval=False)

        if device_code_entry.is_expired():
            return _oauth_error(
                status.HTTP_400_BAD_REQUEST,
                'expired_token',
                'Device code has expired',
            )

        if device_code_entry.status == 'denied':
            return _oauth_error(
                status.HTTP_400_BAD_REQUEST,
                'access_denied',
                'User denied the authorization request',
            )

        if device_code_entry.status == 'pending':
            return _oauth_error(
                status.HTTP_400_BAD_REQUEST,
                'authorization_pending',
                'User has not yet completed authorization',
            )

        if device_code_entry.status == 'authorized':
            # Verify user_id is set (should always be true for authorized status)
            if not device_code_entry.keycloak_user_id:
                logger.error(
                    'Authorized device code missing user_id',
                    extra={'user_code': device_code_entry.user_code},
                )
                return _oauth_error(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'server_error',
                    'User identification missing',
                )

            # Retrieve the specific API key for this device using the user_code
            api_key_store = ApiKeyStore.get_instance()
            device_key_name = f'{API_KEY_NAME} ({device_code_entry.user_code})'
            device_api_key = await api_key_store.retrieve_api_key_by_name(
                device_code_entry.keycloak_user_id, device_key_name
            )

            if not device_api_key:
                logger.error(
                    'No device API key found for authorized device',
                    extra={
                        'user_id': device_code_entry.keycloak_user_id,
                        'user_code': device_code_entry.user_code,
                    },
                )
                return _oauth_error(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'server_error',
                    'API key not found',
                )

            # Return the API key as access_token
            return DeviceTokenResponse(
                access_token=device_api_key,
            )

        # Fallback for unexpected status values
        logger.error(
            'Unknown device code status',
            extra={'status': device_code_entry.status},
        )
        return _oauth_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            'server_error',
            'Unknown device code status',
        )

    except Exception as e:
        logger.exception('Error in device token: %s', str(e))
        return _oauth_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            'server_error',
            'Internal server error',
        )