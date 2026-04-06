async def read_items(token: str | None = Depends(oauth2_scheme)):
    return {"token": token}