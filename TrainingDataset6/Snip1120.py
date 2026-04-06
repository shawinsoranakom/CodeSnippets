def get_user_me(username: str = Depends(get_username, scope="function")):
    return username