async def verify_redirect_uri(
    hass: HomeAssistant, client_id: str, redirect_uri: str
) -> bool:
    """Verify that the client and redirect uri match."""
    try:
        client_id_parts = _parse_client_id(client_id)
    except ValueError:
        return False

    redirect_parts = _parse_url(redirect_uri)

    # Verify redirect url and client url have same scheme and domain.
    is_valid = (
        client_id_parts.scheme == redirect_parts.scheme
        and client_id_parts.netloc == redirect_parts.netloc
    )

    if is_valid:
        return True

    # Whitelist the iOS and Android callbacks so that people can link apps
    # without being connected to the internet.
    if (
        client_id == "https://home-assistant.io/iOS"
        and redirect_uri == "homeassistant://auth-callback"
    ):
        return True

    if client_id == "https://home-assistant.io/android" and redirect_uri in (
        "homeassistant://auth-callback",
        "https://wear.googleapis.com/3p_auth/io.homeassistant.companion.android",
        "https://wear.googleapis-cn.com/3p_auth/io.homeassistant.companion.android",
    ):
        return True

    # IndieAuth 4.2.2 allows for redirect_uri to be on different domain
    # but needs to be specified in link tag when fetching `client_id`.
    redirect_uris = await fetch_redirect_uris(hass, client_id)
    return redirect_uri in redirect_uris