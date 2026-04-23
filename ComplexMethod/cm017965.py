def _extract_and_ocr_sheet_images(
        self, sheet: Any, ocr_service: LLMVisionOCRService
    ) -> list[dict]:
        """
        Extract and OCR images from an Excel sheet.

        Args:
            sheet: openpyxl worksheet
            ocr_service: OCR service

        Returns:
            List of dicts with 'cell_ref' and 'ocr_text'
        """
        results = []

        try:
            # Check if sheet has images
            if hasattr(sheet, "_images"):
                for img in sheet._images:
                    try:
                        # Get image data
                        if hasattr(img, "_data"):
                            image_data = img._data()
                        elif hasattr(img, "image"):
                            # Some versions store it differently
                            image_data = img.image
                        else:
                            continue

                        # Create image stream
                        image_stream = io.BytesIO(image_data)

                        # Get cell reference
                        cell_ref = "unknown"
                        if hasattr(img, "anchor"):
                            anchor = img.anchor
                            if hasattr(anchor, "_from"):
                                from_cell = anchor._from
                                if hasattr(from_cell, "col") and hasattr(
                                    from_cell, "row"
                                ):
                                    # Convert column number to letter
                                    col_letter = self._column_number_to_letter(
                                        from_cell.col
                                    )
                                    cell_ref = f"{col_letter}{from_cell.row + 1}"

                        # Perform OCR
                        ocr_result = ocr_service.extract_text(image_stream)

                        if ocr_result.text.strip():
                            results.append(
                                {
                                    "cell_ref": cell_ref,
                                    "ocr_text": ocr_result.text.strip(),
                                    "backend": ocr_result.backend_used,
                                }
                            )

                    except Exception:
                        continue

        except Exception:
            pass

        return results