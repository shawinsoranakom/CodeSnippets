def process_auth(
    credentials: Annotated[str | None, Security(oauth2_scheme)],
    security_scopes: SecurityScopes,
):
    # This is an incorrect way of using it, this is not checking if the scopes are
    # provided by the token, only if the endpoint is requesting them, but the test
    # here is just to check if FastAPI is indeed registering and passing the scopes
    # correctly when using Security with parameterless dependencies.
    if "a" not in security_scopes.scopes or "b" not in security_scopes.scopes:
        raise HTTPException(detail="a or b not in scopes", status_code=401)
    return {"token": credentials, "scopes": security_scopes.scopes}