def file_after_form(
    city: str = Form(),
    file: bytes = File(),
):
    return {"file_content": file, "city": city}