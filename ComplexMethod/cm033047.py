def _download_and_extract_sections_basic(
    file: dict[str, str],
    service: GoogleDriveService,
    allow_images: bool,
    size_threshold: int,
) -> list[TextSection | ImageSection]:
    """Extract text and images from a Google Drive file."""
    file_id = file["id"]
    file_name = file["name"]
    mime_type = file["mimeType"]
    link = file.get(WEB_VIEW_LINK_KEY, "")

    # For non-Google files, download the file
    # Use the correct API call for downloading files
    # lazy evaluation to only download the file if necessary
    def response_call() -> bytes:
        return download_request(service, file_id, size_threshold)

    if is_gdrive_image_mime_type(mime_type):
        # Skip images if not explicitly enabled
        if not allow_images:
            return []

        # Store images for later processing
        sections: list[TextSection | ImageSection] = []

        def store_image_and_create_section(**kwargs):
            pass

        try:
            section, embedded_id = store_image_and_create_section(
                image_data=response_call(),
                file_id=file_id,
                display_name=file_name,
                media_type=mime_type,
                file_origin=FileOrigin.CONNECTOR,
                link=link,
            )
            sections.append(section)
        except Exception as e:
            logging.error(f"Failed to process image {file_name}: {e}")
        return sections

    # For Google Docs, Sheets, and Slides, export as plain text
    if mime_type in GOOGLE_MIME_TYPES_TO_EXPORT:
        export_mime_type = GOOGLE_MIME_TYPES_TO_EXPORT[mime_type]
        # Use the correct API call for exporting files
        request = service.files().export_media(fileId=file_id, mimeType=export_mime_type)
        response = _download_request(request, file_id, size_threshold)
        if not response:
            logging.warning(f"Failed to export {file_name} as {export_mime_type}")
            return []

        text = response.decode("utf-8")
        return [TextSection(link=link, text=text)]

    # Process based on mime type
    if mime_type == "text/plain":
        try:
            text = response_call().decode("utf-8")
            return [TextSection(link=link, text=text)]
        except UnicodeDecodeError as e:
            logging.warning(f"Failed to extract text from {file_name}: {e}")
            return []

    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":

        def docx_to_text_and_images(*args, **kwargs):
            return "docx_to_text_and_images"

        text, _ = docx_to_text_and_images(io.BytesIO(response_call()))
        return [TextSection(link=link, text=text)]

    elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":

        def xlsx_to_text(*args, **kwargs):
            return "xlsx_to_text"

        text = xlsx_to_text(io.BytesIO(response_call()), file_name=file_name)
        return [TextSection(link=link, text=text)] if text else []

    elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":

        def pptx_to_text(*args, **kwargs):
            return "pptx_to_text"

        text = pptx_to_text(io.BytesIO(response_call()), file_name=file_name)
        return [TextSection(link=link, text=text)] if text else []

    elif mime_type == "application/pdf":

        def read_pdf_file(*args, **kwargs):
            return "read_pdf_file"

        text, _pdf_meta, images = read_pdf_file(io.BytesIO(response_call()))
        pdf_sections: list[TextSection | ImageSection] = [TextSection(link=link, text=text)]

        # Process embedded images in the PDF
        try:
            for idx, (img_data, img_name) in enumerate(images):
                section, embedded_id = store_image_and_create_section(
                    image_data=img_data,
                    file_id=f"{file_id}_img_{idx}",
                    display_name=img_name or f"{file_name} - image {idx}",
                    file_origin=FileOrigin.CONNECTOR,
                )
                pdf_sections.append(section)
        except Exception as e:
            logging.error(f"Failed to process PDF images in {file_name}: {e}")
        return pdf_sections

    # Final attempt at extracting text
    file_ext = get_file_ext(file.get("name", ""))
    if file_ext not in ALL_ACCEPTED_FILE_EXTENSIONS:
        logging.warning(f"Skipping file {file.get('name')} due to extension.")
        return []

    try:

        def extract_file_text(*args, **kwargs):
            return "extract_file_text"

        text = extract_file_text(io.BytesIO(response_call()), file_name)
        return [TextSection(link=link, text=text)]
    except Exception as e:
        logging.warning(f"Failed to extract text from {file_name}: {e}")
        return []