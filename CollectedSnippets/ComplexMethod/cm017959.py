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

        assert isinstance(file_stream, io.IOBase)

        # Read file stream into BytesIO for compatibility with pdfplumber
        pdf_bytes = io.BytesIO(file_stream.read())

        try:
            # Single pass: check every page for form-style content.
            # Pages with tables/forms get rich extraction; plain-text
            # pages are collected separately. page.close() is called
            # after each page to free pdfplumber's cached objects and
            # keep memory usage constant regardless of page count.
            markdown_chunks: list[str] = []
            form_page_count = 0
            plain_page_indices: list[int] = []

            with pdfplumber.open(pdf_bytes) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    page_content = _extract_form_content_from_words(page)

                    if page_content is not None:
                        form_page_count += 1
                        if page_content.strip():
                            markdown_chunks.append(page_content)
                    else:
                        plain_page_indices.append(page_idx)
                        text = page.extract_text()
                        if text and text.strip():
                            markdown_chunks.append(text.strip())

                    page.close()  # Free cached page data immediately

            # If no pages had form-style content, use pdfminer for
            # the whole document (better text spacing for prose).
            if form_page_count == 0:
                pdf_bytes.seek(0)
                markdown = pdfminer.high_level.extract_text(pdf_bytes)
            else:
                markdown = "\n\n".join(markdown_chunks).strip()

        except Exception:
            # Fallback if pdfplumber fails
            pdf_bytes.seek(0)
            markdown = pdfminer.high_level.extract_text(pdf_bytes)

        # Fallback if still empty
        if not markdown:
            pdf_bytes.seek(0)
            markdown = pdfminer.high_level.extract_text(pdf_bytes)

        # Post-process to merge MasterFormat-style partial numbering with following text
        markdown = _merge_partial_numbering_lines(markdown)

        return DocumentConverterResult(markdown=markdown)