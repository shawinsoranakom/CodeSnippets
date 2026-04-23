def async_sign_path(
    hass: HomeAssistant,
    path: str,
    expiration: timedelta,
    *,
    refresh_token_id: str | None = None,
    use_content_user: bool = False,
) -> str:
    """Sign a path for temporary access without auth header."""
    if (secret := hass.data.get(DATA_SIGN_SECRET)) is None:
        secret = hass.data[DATA_SIGN_SECRET] = secrets.token_hex()

    if refresh_token_id is None:
        if use_content_user:
            refresh_token_id = hass.data[STORAGE_KEY]
        elif (
            connection := websocket_api.current_connection.get()
        ) and connection.refresh_token_id:
            refresh_token_id = connection.refresh_token_id
        elif (
            request := current_request.get()
        ) and KEY_HASS_REFRESH_TOKEN_ID in request:
            refresh_token_id = request[KEY_HASS_REFRESH_TOKEN_ID]
        else:
            refresh_token_id = hass.data[STORAGE_KEY]

    url = URL(path)
    now_timestamp = int(time.time())
    expiration_timestamp = now_timestamp + int(expiration.total_seconds())
    params = [itm for itm in url.query.items() if itm[0] not in SAFE_QUERY_PARAMS]
    json_payload = json_bytes(
        {
            "iss": refresh_token_id,
            "path": url.path,
            "params": params,
            "iat": now_timestamp,
            "exp": expiration_timestamp,
        }
    )
    encoded = api_jws.encode(json_payload, secret, "HS256")
    params.append((SIGN_QUERY_PARAM, encoded))
    url = url.with_query(params)
    return f"{url.path}?{url.query_string}"