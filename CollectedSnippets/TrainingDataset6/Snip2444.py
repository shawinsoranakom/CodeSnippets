def get_credentials(
    credentials: Annotated[dict, Security(process_auth, scopes=["a", "b"])],
):
    return credentials