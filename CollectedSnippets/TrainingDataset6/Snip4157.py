async def read_items(token: str | None = Security(oauth2_scheme)):
    if token is None:
        return {"msg": "Create an account first"}
    return {"token": token}