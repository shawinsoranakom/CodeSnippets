async def create_item(
    token: str | None = Security(oauth2_scheme, scopes=["read", "write"]),
):
    return {"token": token}