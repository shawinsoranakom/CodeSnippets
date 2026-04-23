async def get_token(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    return token