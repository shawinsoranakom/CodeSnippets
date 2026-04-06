async def sum_numbers(numbers: Annotated[list[int], Body()]):
    return {"sum": sum(numbers)}