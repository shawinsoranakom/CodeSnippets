async def google_gmail_web_oauth_callback():
    state_id = request.args.get("state")
    error = request.args.get("error")
    source = "gmail"

    error_description = request.args.get("error_description") or error

    if not state_id:
        return await _render_web_oauth_popup("", False, "Missing OAuth state parameter.", source)

    state_cache = REDIS_CONN.get(_web_state_cache_key(state_id, source))
    if not state_cache:
        return await _render_web_oauth_popup(state_id, False, "Authorization session expired. Please restart from the main window.", source)

    state_obj = json.loads(state_cache)
    client_config = state_obj.get("client_config")
    redirect_uri = state_obj.get("redirect_uri", GMAIL_WEB_OAUTH_REDIRECT_URI)
    if not client_config:
        REDIS_CONN.delete(_web_state_cache_key(state_id, source))
        return await _render_web_oauth_popup(state_id, False, "Authorization session was invalid. Please retry.", source)

    if error:
        REDIS_CONN.delete(_web_state_cache_key(state_id, source))
        return await _render_web_oauth_popup(state_id, False, error_description or "Authorization was cancelled.", source)

    code = request.args.get("code")
    if not code:
        return await _render_web_oauth_popup(state_id, False, "Missing authorization code from Google.", source)

    try:
        # TODO(google-oauth): branch scopes/redirect_uri based on source_type (drive vs gmail)
        flow = Flow.from_client_config(client_config, scopes=GOOGLE_SCOPES[DocumentSource.GMAIL])
        flow.redirect_uri = redirect_uri
        flow.fetch_token(code=code)
    except Exception as exc:  # pragma: no cover - defensive
        logging.exception("Failed to exchange Google OAuth code: %s", exc)
        REDIS_CONN.delete(_web_state_cache_key(state_id, source))
        return await _render_web_oauth_popup(state_id, False, "Failed to exchange tokens with Google. Please retry.", source)

    creds_json = flow.credentials.to_json()
    result_payload = {
        "user_id": state_obj.get("user_id"),
        "credentials": creds_json,
    }
    REDIS_CONN.set_obj(_web_result_cache_key(state_id, source), result_payload, WEB_FLOW_TTL_SECS)
    REDIS_CONN.delete(_web_state_cache_key(state_id, source))

    return await _render_web_oauth_popup(state_id, True, "Authorization completed successfully.", source)