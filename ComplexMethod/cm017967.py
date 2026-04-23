def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        if _dependency_exc_info is not None:
            raise MissingDependencyException(
                MISSING_DEPENDENCY_MESSAGE.format(
                    converter=type(self).__name__,
                    extension=".pdf",
                    feature="pdf",
                )
            ) from _dependency_exc_info[1].with_traceback(
                _dependency_exc_info[2]
            )  # type: ignore[union-attr]

        # Get OCR service if available (from kwargs or instance)
        ocr_service: LLMVisionOCRService | None = (
            kwargs.get("ocr_service") or self.ocr_service
        )

        # Read PDF into BytesIO
        file_stream.seek(0)
        pdf_bytes = io.BytesIO(file_stream.read())

        markdown_content = []

        try:
            with pdfplumber.open(pdf_bytes) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    markdown_content.append(f"\n## Page {page_num}\n")

                    # If OCR is enabled, interleave text and images by position
                    if ocr_service:
                        images_on_page = self._extract_page_images(pdf_bytes, page_num)

                        if images_on_page:
                            # Extract text lines with Y positions
                            chars = page.chars
                            if chars:
                                # Group chars into lines based on Y position
                                lines_with_y = []
                                current_line = []
                                current_y = None

                                for char in sorted(
                                    chars, key=lambda c: (c["top"], c["x0"])
                                ):
                                    y = char["top"]
                                    if current_y is None:
                                        current_y = y
                                    elif abs(y - current_y) > 2:  # New line threshold
                                        if current_line:
                                            text = "".join(
                                                [c["text"] for c in current_line]
                                            )
                                            lines_with_y.append(
                                                {"y": current_y, "text": text.strip()}
                                            )
                                        current_line = []
                                        current_y = y
                                    current_line.append(char)

                                # Add last line
                                if current_line:
                                    text = "".join([c["text"] for c in current_line])
                                    lines_with_y.append(
                                        {"y": current_y, "text": text.strip()}
                                    )
                            else:
                                # Fallback: use simple text extraction
                                text_content = page.extract_text() or ""
                                lines_with_y = [
                                    {"y": i * 10, "text": line}
                                    for i, line in enumerate(text_content.split("\n"))
                                ]

                            # OCR all images
                            image_data = []
                            for img_info in images_on_page:
                                ocr_result = ocr_service.extract_text(
                                    img_info["stream"]
                                )
                                if ocr_result.text.strip():
                                    image_data.append(
                                        {
                                            "y_pos": img_info["y_pos"],
                                            "name": img_info["name"],
                                            "ocr_text": ocr_result.text,
                                            "backend": ocr_result.backend_used,
                                            "type": "image",
                                        }
                                    )

                            # Add text items
                            content_items = [
                                {
                                    "y_pos": item["y"],
                                    "text": item["text"],
                                    "type": "text",
                                }
                                for item in lines_with_y
                                if item["text"]
                            ]
                            content_items.extend(image_data)

                            # Sort all items by Y position (top to bottom)
                            content_items.sort(key=lambda x: x["y_pos"])

                            # Build markdown by interleaving text and images
                            for item in content_items:
                                if item["type"] == "text":
                                    markdown_content.append(item["text"])
                                else:  # image
                                    ocr_text = item["ocr_text"]
                                    img_marker = (
                                        f"\n\n*[Image OCR]\n{ocr_text}\n[End OCR]*\n"
                                    )
                                    markdown_content.append(img_marker)
                        else:
                            # No images detected - just extract regular text
                            text_content = page.extract_text() or ""
                            if text_content.strip():
                                markdown_content.append(text_content.strip())
                    else:
                        # No OCR, just extract text
                        text_content = page.extract_text() or ""
                        if text_content.strip():
                            markdown_content.append(text_content.strip())

                # Build final markdown
                markdown = "\n\n".join(markdown_content).strip()

                # Fallback to pdfminer if empty
                if not markdown:
                    pdf_bytes.seek(0)
                    markdown = pdfminer.high_level.extract_text(pdf_bytes)

        except Exception:
            # Fallback to pdfminer
            try:
                pdf_bytes.seek(0)
                markdown = pdfminer.high_level.extract_text(pdf_bytes)
            except Exception:
                markdown = ""

        # Final fallback: If still empty/whitespace and OCR is available,
        # treat as scanned PDF and OCR full pages
        if ocr_service and (not markdown or not markdown.strip()):
            pdf_bytes.seek(0)
            markdown = self._ocr_full_pages(pdf_bytes, ocr_service)

        return DocumentConverterResult(markdown=markdown)