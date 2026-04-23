def catching(d: Annotated[str, Depends(catching_dep)]) -> Any:
    raise CustomError("Simulated error during streaming")