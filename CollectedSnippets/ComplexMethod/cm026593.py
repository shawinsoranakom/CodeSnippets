def append_files_to_content() -> Iterable[ImageBlockParam | DocumentBlockParam]:
        content: list[ImageBlockParam | DocumentBlockParam] = []

        for file_path, mime_type in files:
            if not file_path.exists():
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="wrong_file_path",
                    translation_placeholders={"file_path": file_path.as_posix()},
                )

            if mime_type is None:
                mime_type = guess_file_type(file_path)[0]

            if (
                not mime_type
                or not mime_type.startswith(("image/", "application/pdf"))
                or not model_info.capabilities
                or (
                    mime_type.startswith("image/")
                    and not model_info.capabilities.image_input.supported
                )
                or (
                    mime_type.startswith("application/pdf")
                    and not model_info.capabilities.pdf_input.supported
                )
            ):
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="wrong_file_type",
                    translation_placeholders={
                        "file_path": file_path.as_posix(),
                        "mime_type": mime_type or "unknown",
                        "model": model_info.display_name,
                    },
                )
            if mime_type == "image/jpg":
                mime_type = "image/jpeg"

            base64_file = base64.b64encode(file_path.read_bytes()).decode("utf-8")

            if mime_type.startswith("image/"):
                content.append(
                    ImageBlockParam(
                        type="image",
                        source=Base64ImageSourceParam(
                            type="base64",
                            media_type=mime_type,  # type: ignore[typeddict-item]
                            data=base64_file,
                        ),
                    )
                )
            elif mime_type.startswith("application/pdf"):
                content.append(
                    DocumentBlockParam(
                        type="document",
                        source=Base64PDFSourceParam(
                            type="base64",
                            media_type=mime_type,  # type: ignore[typeddict-item]
                            data=base64_file,
                        ),
                    )
                )

        return content