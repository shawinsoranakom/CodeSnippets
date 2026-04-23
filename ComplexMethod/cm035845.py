async def device_verification_authenticated(
    user_code: str = Form(...),
    user_id: str = Depends(get_user_id),
):
    """Process device verification for authenticated users (called by frontend)."""
    try:
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Authentication required',
            )

        # Validate device code
        device_code_entry = await device_code_store.get_by_user_code(user_code)
        if not device_code_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='The device code is invalid or has expired.',
            )

        if not device_code_entry.is_pending():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='This device code has already been processed.',
            )

        # First, authorize the device code
        success = await device_code_store.authorize_device_code(
            user_code=user_code,
            user_id=user_id,
        )

        if not success:
            logger.error(
                'Failed to authorize device code',
                extra={'user_code': user_code, 'user_id': user_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to authorize the device. Please try again.',
            )

        # Only create API key AFTER successful authorization
        api_key_store = ApiKeyStore.get_instance()
        try:
            # Create a unique API key for this device using user_code in the name
            device_key_name = f'{API_KEY_NAME} ({user_code})'
            await api_key_store.create_api_key(
                user_id,
                name=device_key_name,
                expires_at=datetime.now(UTC) + KEY_EXPIRATION_TIME,
            )
            logger.info(
                'Created new device API key for user after successful authorization',
                extra={'user_id': user_id, 'user_code': user_code},
            )
        except Exception as e:
            logger.exception(
                'Failed to create device API key after authorization: %s', str(e)
            )

            # Clean up: revert the device authorization since API key creation failed
            # This prevents the device from being in an authorized state without an API key
            try:
                await device_code_store.deny_device_code(user_code)
                logger.info(
                    'Reverted device authorization due to API key creation failure',
                    extra={'user_code': user_code, 'user_id': user_id},
                )
            except Exception as cleanup_error:
                logger.exception(
                    'Failed to revert device authorization during cleanup: %s',
                    str(cleanup_error),
                )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to create API key for device access.',
            )

        logger.info(
            'Device code authorized with API key successfully',
            extra={'user_code': user_code, 'user_id': user_id},
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={'message': 'Device authorized successfully!'},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Error in device verification: %s', str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='An unexpected error occurred. Please try again.',
        )