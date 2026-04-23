async def get(
    x: Annotated[float, Query(allow_inf_nan=True)] = 0,
    y: Annotated[float, Query(allow_inf_nan=False)] = 0,
    z: Annotated[float, Query()] = 0,
    b: Annotated[float, Body(allow_inf_nan=False)] = 0,
) -> str:
    return "OK"