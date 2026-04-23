def get_user_items(
        user_me: Annotated[dict, Depends(get_user_me)],
    ):
        call_counts["get_user_items"] += 1
        return {
            "user_items": f"user_items_{call_counts['get_user_items']}",
            "user_me": user_me,
        }