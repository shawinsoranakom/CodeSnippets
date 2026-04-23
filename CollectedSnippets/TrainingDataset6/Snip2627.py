def _get_client_tag(client_id: str | None = Query(None)) -> str | None:
    if client_id is None:
        return None
    return f"{client_id}_tag"