def path_operation(
        user_me: Annotated[dict, Depends(get_user_me)],
        user_items: Annotated[dict, Security(get_user_items, scopes=["items"])],
    ):
        return {
            "user_me": user_me,
            "user_items": user_items,
        }