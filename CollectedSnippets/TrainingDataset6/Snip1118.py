def get_user_me(username: Annotated[str, Depends(get_username, scope="function")]):
    return username