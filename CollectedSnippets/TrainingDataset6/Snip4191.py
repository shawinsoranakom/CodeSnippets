def endpoint(
        db: Annotated[str, Depends(get_db)],
        user: Annotated[str, Security(get_user, scopes=["read"])],
    ):
        return {"db": db}