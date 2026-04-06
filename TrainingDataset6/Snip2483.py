def read_user(
    user_data: tuple[str, list[str]] = Security(get_user, scopes=["foo", "bar"]),
    data: list[int] = Depends(get_data),
):
    return {"user": user_data[0], "scopes": user_data[1], "data": data}