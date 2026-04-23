async def read_users_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user