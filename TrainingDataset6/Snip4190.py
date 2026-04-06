def get_user(db: Annotated[str, Depends(get_db)]):
        return "user"