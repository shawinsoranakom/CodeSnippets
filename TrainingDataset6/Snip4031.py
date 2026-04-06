def get_current_user(oauth_header: str | None = Security(api_key)):
    if oauth_header is None:
        return None
    user = User(username=oauth_header)
    return user