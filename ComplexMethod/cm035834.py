async def __call__(self, request: Request, call_next: Callable):
        keycloak_auth_cookie = request.cookies.get('keycloak_auth')
        logger.debug('request_with_cookie', extra={'cookie': keycloak_auth_cookie})
        try:
            if self._should_attach(request):
                self._check_tos(request)

            response: Response = await call_next(request)
            if not keycloak_auth_cookie:
                return response
            user_auth = self._get_user_auth(request)
            if not user_auth or user_auth.auth_type != AuthType.COOKIE:
                return response
            if user_auth.refreshed:
                if user_auth.access_token is None:
                    return response
                set_response_cookie(
                    request=request,
                    response=response,
                    keycloak_access_token=user_auth.access_token.get_secret_value(),
                    keycloak_refresh_token=user_auth.refresh_token.get_secret_value(),
                    secure=False if request.url.hostname == 'localhost' else True,
                    accepted_tos=user_auth.accepted_tos or False,
                )

                # On re-authentication (token refresh), kick off background sync for GitLab repos
                user_id = await user_auth.get_user_id()
                if user_id:
                    schedule_gitlab_repo_sync(user_id)

            if (
                self._should_attach(request)
                and not request.url.path.startswith('/api/email')
                and request.url.path
                not in ('/api/settings', '/api/logout', '/api/authenticate')
                and not user_auth.email_verified
            ):
                raise EmailNotVerifiedError

            return response
        except EmailNotVerifiedError as e:
            return JSONResponse(
                {'error': str(e) or e.__class__.__name__}, status.HTTP_403_FORBIDDEN
            )
        except NoCredentialsError as e:
            logger.info(e.__class__.__name__)
            # The user is trying to use an expired token or has not logged in. No special event handling is required
            return JSONResponse(
                {'error': str(e) or e.__class__.__name__}, status.HTTP_401_UNAUTHORIZED
            )
        except AuthError as e:
            logger.warning('auth_error', exc_info=True)
            try:
                await self._logout(request)
            except Exception as logout_error:
                logger.debug(str(logout_error))

            # Send a response that deletes the auth cookie if needed
            response = JSONResponse(
                {'error': str(e) or e.__class__.__name__}, status.HTTP_401_UNAUTHORIZED
            )
            if keycloak_auth_cookie:
                response.delete_cookie(
                    key='keycloak_auth',
                    domain=get_cookie_domain(),
                    samesite=get_cookie_samesite(),
                )
            return response