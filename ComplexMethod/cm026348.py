def websocket_delete_all_refresh_tokens(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle delete all refresh tokens request."""
    current_refresh_token: RefreshToken | None = None
    remove_failed = False
    token_type = msg.get("token_type")
    delete_current_token = msg.get("delete_current_token")
    limit_token_types = token_type is not None

    for token in list(connection.user.refresh_tokens.values()):
        if token.id == connection.refresh_token_id:
            # Skip the current refresh token as it has revoke_callback,
            # which cancels/closes the connection.
            # It will be removed after sending the result.
            current_refresh_token = token
            continue
        if limit_token_types and token_type != token.token_type:
            continue
        try:
            hass.auth.async_remove_refresh_token(token)
        except Exception:
            getLogger(__name__).exception("Error during refresh token removal")
            remove_failed = True

    if remove_failed:
        connection.send_error(
            msg["id"], "token_removing_error", "During removal, an error was raised."
        )
    else:
        connection.send_result(msg["id"], {})

    async def _delete_current_token_soon(current_refresh_token: RefreshToken) -> None:
        """Delete the current token after a delay.

        We do not want to delete the current token immediately as it will
        close the connection.

        This is implemented as a tracked task to ensure the token
        is still deleted if Home Assistant is shut down during
        the delay.

        It should not be refactored to use a call_later as that
        would not be tracked and the token would not be deleted
        if Home Assistant was shut down during the delay.
        """
        try:
            await asyncio.sleep(DELETE_CURRENT_TOKEN_DELAY)
        finally:
            # If the task is cancelled because we are shutting down, delete
            # the token right away.
            hass.auth.async_remove_refresh_token(current_refresh_token)

    if (
        delete_current_token
        and current_refresh_token
        and (not limit_token_types or current_refresh_token.token_type == token_type)
    ):
        # Deleting the token will close the connection so we need
        # to do it with a delay in a tracked task to ensure it still
        # happens if Home Assistant is shutting down.
        hass.async_create_task(_delete_current_token_soon(current_refresh_token))