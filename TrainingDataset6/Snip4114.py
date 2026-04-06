async def read_items(token: str | None = Security(oauth2_scheme)):
    return {"token": token}