async def post_multi_part(
    age: Annotated[int | None, Form()] = None,
    file: Annotated[bytes | None, File()] = None,
):
    return {"file": file, "age": age}