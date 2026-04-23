async def oauth_callback(channel):
    """
    Handle the OAuth/OIDC callback for various channels dynamically.
    """
    try:
        channel_config = settings.OAUTH_CONFIG.get(channel)
        if not channel_config:
            raise ValueError(f"Invalid channel name: {channel}")
        auth_cli = get_auth_client(channel_config)

        # Check the state
        state = request.args.get("state")
        if not state or state != session.get("oauth_state"):
            return redirect("/?error=invalid_state")
        session.pop("oauth_state", None)

        # Obtain the authorization code
        code = request.args.get("code")
        if not code:
            return redirect("/?error=missing_code")

        # Exchange authorization code for access token
        if hasattr(auth_cli, "async_exchange_code_for_token"):
            token_info = await auth_cli.async_exchange_code_for_token(code)
        else:
            token_info = auth_cli.exchange_code_for_token(code)
        access_token = token_info.get("access_token")
        if not access_token:
            return redirect("/?error=token_failed")

        id_token = token_info.get("id_token")

        # Fetch user info
        if hasattr(auth_cli, "async_fetch_user_info"):
            user_info = await auth_cli.async_fetch_user_info(access_token, id_token=id_token)
        else:
            user_info = auth_cli.fetch_user_info(access_token, id_token=id_token)
        if not user_info.email:
            return redirect("/?error=email_missing")

        # Login or register
        users = UserService.query(email=user_info.email)
        user_id = get_uuid()

        if not users:
            try:
                try:
                    avatar = await download_img(user_info.avatar_url)
                except Exception as e:
                    logging.exception(e)
                    avatar = ""

                users = user_register(
                    user_id,
                    {
                        "access_token": get_uuid(),
                        "email": user_info.email,
                        "avatar": avatar,
                        "nickname": user_info.nickname,
                        "login_channel": channel,
                        "last_login_time": get_format_time(),
                        "is_superuser": False,
                    },
                )

                if not users:
                    raise Exception(f"Failed to register {user_info.email}")
                if len(users) > 1:
                    raise Exception(f"Same email: {user_info.email} exists!")

                # Try to log in
                user = users[0]
                login_user(user)
                return redirect(f"/?auth={user.get_id()}")

            except Exception as e:
                rollback_user_registration(user_id)
                logging.exception(e)
                return redirect(f"/?error={str(e)}")

        # User exists, try to log in
        user = users[0]
        user.access_token = get_uuid()
        if user and hasattr(user, 'is_active') and user.is_active == "0":
            return redirect("/?error=user_inactive")

        login_user(user)
        user.save()
        return redirect(f"/?auth={user.get_id()}")
    except Exception as e:
        logging.exception(e)
        return redirect(f"/?error={str(e)}")