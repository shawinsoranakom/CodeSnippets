async def get_ayrshare_sso_url(
    user_id: Annotated[str, Security(get_user_id)],
) -> AyrshareSSOResponse:
    """
    Generate an SSO URL for Ayrshare social media integration.

    Returns:
        dict: Contains the SSO URL for Ayrshare integration
    """
    try:
        client = AyrshareClient()
    except MissingConfigError:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ayrshare integration is not configured",
        )

    # Ayrshare profile key is stored in the credentials store
    # It is generated when creating a new profile, if there is no profile key,
    # we create a new profile and store the profile key in the credentials store

    user_integrations: UserIntegrations = await get_user_integrations(user_id)
    profile_key = user_integrations.managed_credentials.ayrshare_profile_key

    if not profile_key:
        logger.debug(f"Creating new Ayrshare profile for user {user_id}")
        try:
            profile = await client.create_profile(
                title=f"User {user_id}", messaging_active=True
            )
            profile_key = profile.profileKey
            await creds_manager.store.set_ayrshare_profile_key(user_id, profile_key)
        except Exception as e:
            logger.error(f"Error creating Ayrshare profile for user {user_id}: {e}")
            raise HTTPException(
                status_code=HTTP_502_BAD_GATEWAY,
                detail="Failed to create Ayrshare profile",
            )
    else:
        logger.debug(f"Using existing Ayrshare profile for user {user_id}")

    profile_key_str = (
        profile_key.get_secret_value()
        if isinstance(profile_key, SecretStr)
        else str(profile_key)
    )

    private_key = settings.secrets.ayrshare_jwt_key
    # Ayrshare JWT expiry is 2880 minutes (48 hours)
    max_expiry_minutes = 2880
    try:
        logger.debug(f"Generating Ayrshare JWT for user {user_id}")
        jwt_response = await client.generate_jwt(
            private_key=private_key,
            profile_key=profile_key_str,
            allowed_social=[
                # NOTE: We are enabling platforms one at a time
                # to speed up the development process
                # SocialPlatform.FACEBOOK,
                SocialPlatform.TWITTER,
                SocialPlatform.LINKEDIN,
                SocialPlatform.INSTAGRAM,
                SocialPlatform.YOUTUBE,
                # SocialPlatform.REDDIT,
                # SocialPlatform.TELEGRAM,
                # SocialPlatform.GOOGLE_MY_BUSINESS,
                # SocialPlatform.PINTEREST,
                SocialPlatform.TIKTOK,
                # SocialPlatform.BLUESKY,
                # SocialPlatform.SNAPCHAT,
                # SocialPlatform.THREADS,
            ],
            expires_in=max_expiry_minutes,
            verify=True,
        )
    except Exception as e:
        logger.error(f"Error generating Ayrshare JWT for user {user_id}: {e}")
        raise HTTPException(
            status_code=HTTP_502_BAD_GATEWAY, detail="Failed to generate JWT"
        )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=max_expiry_minutes)
    return AyrshareSSOResponse(sso_url=jwt_response.url, expires_at=expires_at)
