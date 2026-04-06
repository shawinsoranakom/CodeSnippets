def broken(d: Annotated[str, Depends(broken_dep)]) -> Any:
    return {"message": "all good?"}