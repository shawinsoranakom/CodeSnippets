def _build_pdf_overlay_page(self, width: float, height: float, page_number: int):
        if not self._should_apply_pdf_overlay():
            return None

        from pypdf import PdfReader
        from reportlab.lib.colors import Color
        from reportlab.pdfgen import canvas as pdf_canvas

        buffer = BytesIO()
        overlay = pdf_canvas.Canvas(buffer, pagesize=(width, height))
        overlay_font = self._get_pdf_overlay_font_name()

        if self._param.watermark_text:
            overlay.saveState()
            if hasattr(overlay, "setFillAlpha"):
                overlay.setFillAlpha(0.15)
            overlay.setFillColor(Color(0.6, 0.6, 0.6))
            overlay.setFont(overlay_font, 48)
            overlay.translate(width / 2, height / 2)
            overlay.rotate(45)
            overlay.drawCentredString(0, 0, self._param.watermark_text)
            overlay.restoreState()

        overlay.setFont(overlay_font, self._overlay_font_size)
        overlay.setFillColor(Color(0.35, 0.35, 0.35))

        if self._param.header_text:
            overlay.drawString(
                self._overlay_margin,
                height - self._overlay_margin + 8,
                self._param.header_text,
            )

        if self._param.footer_text:
            overlay.drawString(
                self._overlay_margin,
                self._overlay_margin - 8,
                self._param.footer_text,
            )

        if self._param.add_timestamp:
            overlay.drawCentredString(
                width / 2,
                self._overlay_margin - 8,
                self._get_timestamp_text(),
            )

        if self._param.add_page_numbers:
            overlay.drawRightString(
                width - self._overlay_margin,
                self._overlay_margin - 8,
                f"Page {page_number}",
            )

        overlay.save()
        buffer.seek(0)
        return PdfReader(buffer).pages[0]