async def keycloak_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    user_authorizer: UserAuthorizer = depends_user_authorizer(),
):
    # Extract redirect URL, reCAPTCHA token, and invitation token from state
    redirect_url, recaptcha_token, invitation_token = _extract_oauth_state(state)

    if redirect_url is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Missing state in request params',
        )

    if not code:
        # check if this is a forward from the account linking page
        if (
            error == 'temporarily_unavailable'
            and error_description == 'authentication_expired'
        ):
            return RedirectResponse(redirect_url, status_code=302)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Missing code in request params',
        )

    web_url = get_web_url(request)
    redirect_uri = web_url + request.url.path

    (
        keycloak_access_token,
        keycloak_refresh_token,
    ) = await token_manager.get_keycloak_tokens(code, redirect_uri)
    if not keycloak_access_token or not keycloak_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Problem retrieving Keycloak tokens',
        )

    user_info = await token_manager.get_user_info(keycloak_access_token)
    logger.debug(f'user_info: {user_info}')
    if ROLE_CHECK_ENABLED and user_info.roles is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing required role'
        )

    authorization = await user_authorizer.authorize_user(user_info)
    if not authorization.success:
        # For duplicate_email errors, clean up the newly created Keycloak user
        # (only if they're not already in our UserStore, i.e., they're a new user)
        if authorization.error_detail == 'duplicate_email':
            try:
                existing_user = await UserStore.get_user_by_id(user_info.sub)
                if not existing_user:
                    # New user created during OAuth should be deleted from Keycloak
                    await token_manager.delete_keycloak_user(user_info.sub)
                    logger.info(
                        f'Deleted orphaned Keycloak user {user_info.sub} '
                        'after duplicate_email rejection'
                    )
            except Exception as e:
                # Log but don't fail - user should still get 401 response
                logger.warning(
                    f'Failed to clean up orphaned Keycloak user {user_info.sub}: {e}'
                )
        # Return unauthorized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=authorization.error_detail,
        )

    email = user_info.email
    user_id = user_info.sub
    user_info_dict = user_info.model_dump(exclude_none=True)
    user = await UserStore.get_user_by_id(user_id)
    if not user:
        user = await UserStore.create_user(user_id, user_info_dict)
    else:
        # Existing user — gradually backfill contact_name if it still has a username-style value
        await UserStore.backfill_contact_name(user_id, user_info_dict)
        await UserStore.backfill_user_email(user_id, user_info_dict)

    if not user:
        logger.error(f'Failed to authenticate user {user_info.email}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Failed to authenticate user {user_info.email}',
        )

    logger.info(f'Logging in user {str(user.id)} in org {user.current_org_id}')

    # reCAPTCHA verification with Account Defender
    if RECAPTCHA_SITE_KEY:
        if not recaptcha_token:
            logger.warning(
                'recaptcha_token_missing',
                extra={
                    'user_id': user_id,
                    'email': email,
                },
            )
            error_url = f'{web_url}/login?recaptcha_blocked=true'
            return RedirectResponse(error_url, status_code=302)

        user_ip = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('User-Agent', '')

        # Handle X-Forwarded-For for proxied requests
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            user_ip = forwarded_for.split(',')[0].strip()

        try:
            result = recaptcha_service.create_assessment(
                token=recaptcha_token,
                action='LOGIN',
                user_ip=user_ip,
                user_agent=user_agent,
                email=email,
                user_id=user_id,
            )

            if not result.allowed:
                logger.warning(
                    'recaptcha_blocked_at_callback',
                    extra={
                        'user_ip': user_ip,
                        'score': result.score,
                        'user_id': user_id,
                    },
                )
                # Redirect to home with error parameter
                error_url = f'{web_url}/login?recaptcha_blocked=true'
                return RedirectResponse(error_url, status_code=302)

        except Exception as e:
            logger.exception(f'reCAPTCHA verification error at callback: {e}')
            # Fail open - continue with login if reCAPTCHA service unavailable

    # Check email verification status
    email_verified = user_info.email_verified or False
    if not email_verified:
        # Send verification email with rate limiting to prevent abuse
        # Users who repeatedly login without verifying would otherwise trigger
        # unlimited verification emails
        # Import locally to avoid circular import with email.py
        from server.routes.email import verify_email

        # Rate limit verification emails during auth flow (60 seconds per user)
        # This is separate from the manual resend rate limit which uses 30 seconds
        rate_limited = False
        try:
            await check_rate_limit_by_user_id(
                request=request,
                key_prefix='auth_verify_email',
                user_id=user_id,
                user_rate_limit_seconds=60,
                ip_rate_limit_seconds=120,
            )
            await verify_email(request=request, user_id=user_id, is_auth_flow=True)
        except HTTPException as e:
            if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                # Rate limited - still redirect to verification page but don't send email
                rate_limited = True
                logger.info(
                    f'Rate limited verification email for user {user_id} during auth flow'
                )
            else:
                raise

        verification_redirect_url = (
            f'{web_url}/login?email_verification_required=true&user_id={user_id}'
        )
        if rate_limited:
            verification_redirect_url = f'{verification_redirect_url}&rate_limited=true'

        # Preserve invitation token so it can be included in OAuth state after verification
        if invitation_token:
            verification_redirect_url = (
                f'{verification_redirect_url}&invitation_token={invitation_token}'
            )
        response = RedirectResponse(verification_redirect_url, status_code=302)
        return response

    # default to github IDP for now.
    # TODO: remove default once Keycloak is updated universally with the new attribute.
    idp: str = user_info.identity_provider or ProviderType.GITHUB.value
    logger.info(f'Full IDP is {idp}')
    idp_type = 'oidc'
    if ':' in idp:
        idp, idp_type = idp.rsplit(':', 1)
        idp_type = idp_type.lower()

    await token_manager.store_idp_tokens(
        ProviderType(idp), user_id, keycloak_access_token
    )

    valid_offline_token = (
        await token_manager.validate_offline_token(user_id=user_info.sub)
        if idp_type != 'saml'
        else True
    )

    logger.debug(
        f'keycloakAccessToken: {keycloak_access_token}, keycloakUserId: {user_id}'
    )

    # adding in posthog tracking

    # If this is a feature environment, add "FEATURE_" prefix to user_id for PostHog
    posthog_user_id = f'FEATURE_{user_id}' if IS_FEATURE_ENV else user_id

    try:
        posthog.set(
            distinct_id=posthog_user_id,
            properties={
                'user_id': posthog_user_id,
                'original_user_id': user_id,
                'is_feature_env': IS_FEATURE_ENV,
            },
        )
    except Exception as e:
        logger.error(
            'auth:posthog_set:failed',
            extra={
                'user_id': user_id,
                'error': str(e),
            },
        )
        # Continue execution as this is not critical

    logger.info(
        'user_logged_in',
        extra={
            'idp': idp,
            'idp_type': idp_type,
            'posthog_user_id': posthog_user_id,
            'is_feature_env': IS_FEATURE_ENV,
        },
    )

    if not valid_offline_token:
        param_str = urlencode(
            {
                'client_id': KEYCLOAK_CLIENT_ID,
                'response_type': 'code',
                'kc_idp_hint': idp,
                'redirect_uri': f'{web_url}/oauth/keycloak/offline/callback',
                'scope': 'openid email profile offline_access',
                'state': state,
            }
        )
        redirect_url = (
            f'{KEYCLOAK_SERVER_URL_EXT}/realms/{KEYCLOAK_REALM_NAME}/protocol/openid-connect/auth'
            f'?{param_str}'
        )

    has_accepted_tos = user.accepted_tos is not None

    # Process invitation token if present (after email verification but before TOS)
    if invitation_token:
        try:
            logger.info(
                'Processing invitation token during auth callback',
                extra={
                    'user_id': user_id,
                    'invitation_token_prefix': invitation_token[:10] + '...',
                },
            )

            await OrgInvitationService.accept_invitation(
                invitation_token, parse_uuid(user_id)
            )
            logger.info(
                'Invitation accepted during auth callback',
                extra={'user_id': user_id},
            )

        except InvitationExpiredError:
            logger.warning(
                'Invitation expired during auth callback',
                extra={'user_id': user_id},
            )
            # Add query param to redirect URL
            if '?' in redirect_url:
                redirect_url = f'{redirect_url}&invitation_expired=true'
            else:
                redirect_url = f'{redirect_url}?invitation_expired=true'

        except InvitationInvalidError as e:
            logger.warning(
                'Invalid invitation during auth callback',
                extra={'user_id': user_id, 'error': str(e)},
            )
            if '?' in redirect_url:
                redirect_url = f'{redirect_url}&invitation_invalid=true'
            else:
                redirect_url = f'{redirect_url}?invitation_invalid=true'

        except UserAlreadyMemberError:
            logger.info(
                'User already member during invitation acceptance',
                extra={'user_id': user_id},
            )
            if '?' in redirect_url:
                redirect_url = f'{redirect_url}&already_member=true'
            else:
                redirect_url = f'{redirect_url}?already_member=true'

        except EmailMismatchError as e:
            logger.warning(
                'Email mismatch during auth callback invitation acceptance',
                extra={'user_id': user_id, 'error': str(e)},
            )
            if '?' in redirect_url:
                redirect_url = f'{redirect_url}&email_mismatch=true'
            else:
                redirect_url = f'{redirect_url}?email_mismatch=true'

        except Exception as e:
            logger.exception(
                'Unexpected error processing invitation during auth callback',
                extra={'user_id': user_id, 'error': str(e)},
            )
            # Don't fail the login if invitation processing fails
            if '?' in redirect_url:
                redirect_url = f'{redirect_url}&invitation_error=true'
            else:
                redirect_url = f'{redirect_url}?invitation_error=true'

    # If the user hasn't accepted the TOS, redirect to the TOS page
    if not has_accepted_tos:
        encoded_redirect_url = quote(redirect_url, safe='')
        tos_redirect_url = f'{web_url}/accept-tos?redirect_url={encoded_redirect_url}'
        if invitation_token:
            tos_redirect_url = f'{tos_redirect_url}&invitation_success=true'
        response = RedirectResponse(tos_redirect_url, status_code=302)
    else:
        # User has accepted TOS - check if they need onboarding
        # Only redirect to onboarding if user has a valid offline token,
        # otherwise they need to complete the Keycloak offline token flow first
        if valid_offline_token and await _should_redirect_to_onboarding(user_id, user):
            redirect_url = f'{web_url}/onboarding'
            logger.info(
                'Redirecting returning user to onboarding',
                extra={'user_id': user_id, 'deployment_mode': DEPLOYMENT_MODE},
            )
        if invitation_token:
            if '?' in redirect_url:
                redirect_url = f'{redirect_url}&invitation_success=true'
            else:
                redirect_url = f'{redirect_url}?invitation_success=true'
        response = RedirectResponse(redirect_url, status_code=302)

    set_response_cookie(
        request=request,
        response=response,
        keycloak_access_token=keycloak_access_token,
        keycloak_refresh_token=keycloak_refresh_token,
        secure=True if web_url.startswith('https') else False,
        accepted_tos=has_accepted_tos,
    )

    # Sync GitLab repos & set up webhooks
    # Use Keycloak access token (first-time users lack offline token at this stage)
    # Normally, offline token is used to fetch GitLab token via user_id
    schedule_gitlab_repo_sync(user_id, SecretStr(keycloak_access_token))
    return response