async def get(foo: Annotated[int, Query(gt=2), Query(lt=10)]):
        return foo