def app_fixture(call_counts: dict[str, int]):
    def get_db_session():
        call_counts["get_db_session"] += 1
        return f"db_session_{call_counts['get_db_session']}"

    def get_current_user(
        security_scopes: SecurityScopes,
        db_session: Annotated[str, Depends(get_db_session)],
    ):
        call_counts["get_current_user"] += 1
        return {
            "user": f"user_{call_counts['get_current_user']}",
            "scopes": security_scopes.scopes,
            "db_session": db_session,
        }

    def get_user_me(
        current_user: Annotated[dict, Security(get_current_user, scopes=["me"])],
    ):
        call_counts["get_user_me"] += 1
        return {
            "user_me": f"user_me_{call_counts['get_user_me']}",
            "current_user": current_user,
        }

    def get_user_items(
        user_me: Annotated[dict, Depends(get_user_me)],
    ):
        call_counts["get_user_items"] += 1
        return {
            "user_items": f"user_items_{call_counts['get_user_items']}",
            "user_me": user_me,
        }

    app = FastAPI()

    @app.get("/")
    def path_operation(
        user_me: Annotated[dict, Depends(get_user_me)],
        user_items: Annotated[dict, Security(get_user_items, scopes=["items"])],
    ):
        return {
            "user_me": user_me,
            "user_items": user_items,
        }

    return app