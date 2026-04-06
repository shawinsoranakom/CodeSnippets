def dep_b(a: Annotated[int, Depends(dep_a)]):
    return a + 2