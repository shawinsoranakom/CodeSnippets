def file_before_form(
    file: bytes = File(),
    city: str = Form(),
):
    return {"file_content": file, "city": city}