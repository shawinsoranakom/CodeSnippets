def read_root(c: Annotated[Any, Depends(get_db)]):
        return {"c": str(c)}