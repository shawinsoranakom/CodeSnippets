async def get_llm_api_key_for_byor(
    user_id: str = Depends(get_user_id),
) -> LlmApiKeyResponse:
    """Get the LLM API key for BYOR (Bring Your Own Runtime) for the authenticated user.

    This endpoint validates that the key exists in LiteLLM before returning it.
    If validation fails, it automatically generates a new key to ensure users
    always receive a working key.

    Returns 402 Payment Required if BYOR export is not enabled for the user's org.
    """
    try:
        # Check if BYOR export is enabled for the user's org
        if not await OrgService.check_byor_export_enabled(user_id):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail='BYOR key export is not enabled. Purchase credits to enable this feature.',
            )

        # Check if the BYOR key exists in the database
        byor_key = await get_byor_key_from_db(user_id)
        if byor_key:
            # Validate that the key is actually registered in LiteLLM
            is_valid = await LiteLlmManager.verify_key(byor_key, user_id)
            if is_valid:
                return LlmApiKeyResponse(key=byor_key)
            else:
                # Key exists in DB but is invalid in LiteLLM - regenerate it
                logger.warning(
                    'BYOR key found in database but invalid in LiteLLM - regenerating',
                    extra={
                        'user_id': user_id,
                        'key_prefix': byor_key[:10] + '...'
                        if len(byor_key) > 10
                        else byor_key,
                    },
                )
                # Delete the invalid key from LiteLLM (best effort, don't fail if it doesn't exist)
                await delete_byor_key_from_litellm(user_id, byor_key)
                # Fall through to generate a new key

        # Generate a new key for BYOR (either no key exists or validation failed)
        key = await generate_byor_key(user_id)
        if key:
            # Store the key in the database
            await store_byor_key_in_db(user_id, key)
            logger.info(
                'Successfully generated and stored new BYOR key',
                extra={'user_id': user_id},
            )
            return LlmApiKeyResponse(key=key)
        else:
            logger.error(
                'Failed to generate new BYOR LLM API key',
                extra={'user_id': user_id},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to generate new BYOR LLM API key',
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception('Error retrieving BYOR LLM API key', extra={'error': str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve BYOR LLM API key',
        )