async def check_feature_flag(
        user_id: str | None = Security(get_optional_user_id),
    ) -> None:
        """Check if feature flag is enabled for the user.

        The user_id is automatically injected from JWT authentication if present,
        or None for anonymous access.
        """
        # For routes that don't require authentication, use anonymous context
        check_user_id = user_id or "anonymous"

        if not is_configured():
            logger.debug(
                f"LaunchDarkly not configured, using default {flag_key.value}={default}"
            )
            if not default:
                raise HTTPException(status_code=404, detail="Feature not available")
            return

        try:
            client = get_client()
            if not client.is_initialized():
                logger.debug(
                    f"LaunchDarkly not initialized, using default {flag_key.value}={default}"
                )
                if not default:
                    raise HTTPException(status_code=404, detail="Feature not available")
                return

            is_enabled = await is_feature_enabled(flag_key, check_user_id, default)

            if not is_enabled:
                raise HTTPException(status_code=404, detail="Feature not available")
        except Exception as e:
            logger.warning(
                f"LaunchDarkly error for flag {flag_key.value}: {e}, using default={default}"
            )
            raise HTTPException(status_code=500, detail="Failed to check feature flag")