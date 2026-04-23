def _get_structure(self, service, document_id: str, detailed: bool) -> dict:
        doc = service.documents().get(documentId=document_id).execute()
        body = doc.get("body", {})
        content = body.get("content", [])

        segments: list[dict] = []
        structure_body: list[dict] = []

        for element in content:
            start_index = element.get("startIndex")
            end_index = element.get("endIndex")

            if "paragraph" in element:
                paragraph = element["paragraph"]
                text = self._extract_paragraph_text(paragraph)
                style_info = self._get_paragraph_style(paragraph)

                # Determine segment type
                if style_info.get("heading_level"):
                    seg_type = "heading"
                    segment = {
                        "type": seg_type,
                        "level": style_info["heading_level"],
                        "text": text,
                        "start_index": start_index,
                        "end_index": end_index,
                    }
                else:
                    seg_type = "paragraph"
                    segment = {
                        "type": seg_type,
                        "text": text,
                        "start_index": start_index,
                        "end_index": end_index,
                    }

                # Skip empty paragraphs (just newlines)
                if text.strip():
                    segments.append(segment)

                if detailed:
                    detailed_seg = segment.copy()
                    detailed_seg["style"] = paragraph.get("paragraphStyle", {})
                    structure_body.append(detailed_seg)

            elif "table" in element:
                table = element.get("table", {})
                table_rows = table.get("tableRows", [])

                segment = {
                    "type": "table",
                    "rows": len(table_rows),
                    "columns": table.get("columns", 0),
                    "start_index": start_index,
                    "end_index": end_index,
                }
                segments.append(segment)

                if detailed:
                    structure_body.append(self._process_table_detailed(element))

            elif "sectionBreak" in element:
                # Skip section breaks in simple mode, include in detailed
                if detailed:
                    structure_body.append(
                        {
                            "type": "section_break",
                            "start_index": start_index,
                            "end_index": end_index,
                        }
                    )

            elif "tableOfContents" in element:
                segment = {
                    "type": "table_of_contents",
                    "start_index": start_index,
                    "end_index": end_index,
                }
                segments.append(segment)

                if detailed:
                    structure_body.append(segment)

        result = {
            "segments": segments,
            "structure": {"body": structure_body} if detailed else {},
        }

        return result