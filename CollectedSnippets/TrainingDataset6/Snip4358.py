def call(test: Annotated[str, Depends(Dep())]):
        return {"test": test}