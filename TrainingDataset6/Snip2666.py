def file_list_after_form(
    city: Annotated[str, Form()],
    files: Annotated[list[bytes], File()],
):
    return {"file_contents": files, "city": city}