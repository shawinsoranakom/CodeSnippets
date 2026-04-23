def _ocr_full_pages(
        self, pdf_bytes: io.BytesIO, ocr_service: LLMVisionOCRService
    ) -> str:
        """
        Fallback for scanned PDFs: Convert entire pages to images and OCR them.
        Used when text extraction returns empty/whitespace results.

        Args:
            pdf_bytes: PDF file as BytesIO
            ocr_service: OCR service to use

        Returns:
            Markdown text extracted from OCR of full pages
        """
        markdown_parts = []

        try:
            pdf_bytes.seek(0)
            with pdfplumber.open(pdf_bytes) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        markdown_parts.append(f"\n## Page {page_num}\n")

                        # Render page to image
                        page_img = page.to_image(resolution=300)
                        img_stream = io.BytesIO()
                        page_img.original.save(img_stream, format="PNG")
                        img_stream.seek(0)

                        # Run OCR
                        ocr_result = ocr_service.extract_text(img_stream)

                        if ocr_result.text.strip():
                            text = ocr_result.text.strip()
                            markdown_parts.append(f"*[Image OCR]\n{text}\n[End OCR]*")
                        else:
                            markdown_parts.append(
                                "*[No text could be extracted from this page]*"
                            )

                    except Exception as e:
                        markdown_parts.append(
                            f"*[Error processing page {page_num}: {str(e)}]*"
                        )
                        continue

        except Exception:
            # pdfplumber failed (e.g. malformed EOF) — try PyMuPDF for rendering
            markdown_parts = []
            try:
                import fitz  # PyMuPDF

                pdf_bytes.seek(0)
                doc = fitz.open(stream=pdf_bytes.read(), filetype="pdf")
                for page_num in range(1, doc.page_count + 1):
                    try:
                        markdown_parts.append(f"\n## Page {page_num}\n")
                        page = doc[page_num - 1]
                        mat = fitz.Matrix(300 / 72, 300 / 72)  # 300 DPI
                        pix = page.get_pixmap(matrix=mat)
                        img_stream = io.BytesIO(pix.tobytes("png"))
                        img_stream.seek(0)

                        ocr_result = ocr_service.extract_text(img_stream)

                        if ocr_result.text.strip():
                            text = ocr_result.text.strip()
                            markdown_parts.append(f"*[Image OCR]\n{text}\n[End OCR]*")
                        else:
                            markdown_parts.append(
                                "*[No text could be extracted from this page]*"
                            )

                    except Exception as e:
                        markdown_parts.append(
                            f"*[Error processing page {page_num}: {str(e)}]*"
                        )
                        continue
                doc.close()
            except Exception:
                return "*[Error: Could not process scanned PDF]*"

        return "\n\n".join(markdown_parts).strip()