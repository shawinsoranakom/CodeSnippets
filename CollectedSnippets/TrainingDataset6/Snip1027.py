async def sum_numbers(numbers: list[int] = Body()):
    return {"sum": sum(numbers)}