def read_root(c: Annotated[Any, Depends(module.dependency_c)]):
        return {"c": str(c)}