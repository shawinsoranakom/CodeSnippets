async def start_google_web_oauth():
    source = request.args.get("type", "google-drive")
    if source not in ("google-drive", "gmail"):
        return get_json_result(code=RetCode.ARGUMENT_ERROR, message="Invalid Google OAuth type.")

    req = await get_request_json()

    if source == "gmail":
        default_redirect_uri = GMAIL_WEB_OAUTH_REDIRECT_URI
        scopes = GOOGLE_SCOPES[DocumentSource.GMAIL]
    else:
        default_redirect_uri = GOOGLE_DRIVE_WEB_OAUTH_REDIRECT_URI
        scopes = GOOGLE_SCOPES[DocumentSource.GOOGLE_DRIVE]

    redirect_uri = req.get("redirect_uri", default_redirect_uri)
    if isinstance(redirect_uri, str):
        redirect_uri = redirect_uri.strip()

    if not redirect_uri:
        return get_json_result(
            code=RetCode.SERVER_ERROR,
            message="Google OAuth redirect URI is not configured on the server.",
        )

    raw_credentials = req.get("credentials", "")

    try:
        credentials = _load_credentials(raw_credentials)
        print(credentials)
    except ValueError as exc:
        return get_json_result(code=RetCode.ARGUMENT_ERROR, message=str(exc))

    if credentials.get("refresh_token"):
        return get_json_result(
            code=RetCode.ARGUMENT_ERROR,
            message="Uploaded credentials already include a refresh token.",
        )

    try:
        client_config = _get_web_client_config(credentials)
    except ValueError as exc:
        return get_json_result(code=RetCode.ARGUMENT_ERROR, message=str(exc))

    flow_id = str(uuid.uuid4())
    try:
        flow = Flow.from_client_config(client_config, scopes=scopes)
        flow.redirect_uri = redirect_uri
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=flow_id,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logging.exception("Failed to create Google OAuth flow: %s", exc)
        return get_json_result(
            code=RetCode.SERVER_ERROR,
            message="Failed to initialize Google OAuth flow. Please verify the uploaded client configuration.",
        )

    cache_payload = {
        "user_id": current_user.id,
        "client_config": client_config,
        "redirect_uri": redirect_uri,
        "created_at": int(time.time()),
    }
    REDIS_CONN.set_obj(_web_state_cache_key(flow_id, source), cache_payload, WEB_FLOW_TTL_SECS)

    return get_json_result(
        data={
            "flow_id": flow_id,
            "authorization_url": authorization_url,
            "expires_in": WEB_FLOW_TTL_SECS,
        }
    )