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