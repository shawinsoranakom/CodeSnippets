def get_user_me(
        current_user: Annotated[dict, Security(get_current_user, scopes=["me"])],
    ):
        call_counts["get_user_me"] += 1
        return {
            "user_me": f"user_me_{call_counts['get_user_me']}",
            "current_user": current_user,
        }