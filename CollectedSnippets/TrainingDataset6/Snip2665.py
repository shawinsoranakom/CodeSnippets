def file_list_before_form(
    files: Annotated[list[bytes], File()],
    city: Annotated[str, Form()],
):
    return {"file_contents": files, "city": city}