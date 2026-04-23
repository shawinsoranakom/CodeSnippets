def foo_handler(
    client_key: str = Depends(_get_client_key),
    client_tag: str | None = Depends(_get_client_tag),
):
    return {"client_id": client_key, "client_tag": client_tag}