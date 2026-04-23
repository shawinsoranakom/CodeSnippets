def split_file_attachments(files: list[dict] | None, raw: bool = False) -> tuple[list[str], list[str] | list[dict]]:
    if not files:
        return [], []

    text_attachments = []
    if raw:
        file_contents, image_files = FileService.get_files(files, raw=True)
        for content in file_contents:
            if not isinstance(content, str):
                content = str(content)
            text_attachments.append(content)
        return text_attachments, image_files

    image_attachments = []
    for content in FileService.get_files(files, raw=False):
        if not isinstance(content, str):
            content = str(content)
        if content.strip().startswith("data:"):
            image_attachments.append(content.strip())
            continue
        text_attachments.append(content)
    return text_attachments, image_attachments