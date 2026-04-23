def extract_line_records(self):
        # Normalize all upstream payloads into an ordered record stream.
        # Level resolution and chunk construction operate on this stream only,
        # so strategy code does not depend on source-specific output layouts.
        if self.from_upstream.output_format == "markdown":
            payload = self.from_upstream.markdown_result or ""
            return [{"text": line, "doc_type_kwd": "text", "img_id": None, "layout": "", PDF_POSITIONS_KEY: []} for line in payload.split("\n") if line]

        if self.from_upstream.output_format == "text":
            payload = self.from_upstream.text_result or ""
            return [{"text": line, "doc_type_kwd": "text", "img_id": None, "layout": "", PDF_POSITIONS_KEY: []} for line in payload.split("\n") if line]

        if self.from_upstream.output_format == "html":
            payload = self.from_upstream.html_result or ""
            return [{"text": line, "doc_type_kwd": "text", "img_id": None, "layout": "", PDF_POSITIONS_KEY: []} for line in payload.split("\n") if line]

        items = self.from_upstream.chunks if self.from_upstream.output_format == "chunks" else self.from_upstream.json_result
        return [
            {
                "text": str(item.get("text") or ""),
                "doc_type_kwd": str(item.get("doc_type_kwd") or "text"),
                "img_id": item.get("img_id"),
                "layout": "{} {}".format(item.get("layout_type", ""), item.get("layoutno", "")).strip(),
                PDF_POSITIONS_KEY: extract_pdf_positions(item),
            }
            for item in items or []
        ]