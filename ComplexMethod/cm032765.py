def build_chunks_from_record_groups(self, record_groups):
        # Strategy code decides record grouping. This method materializes each
        # group into the output chunk representation. For PDF-like inputs, the
        # chunk box is defined by merged source positions and the text payload
        # is normalized by removing parser tags.
        if self.from_upstream.output_format in ["markdown", "text", "html"]:
            return [
                {"text": "".join(record["text"] + "\n" for record in records)}
                for records in record_groups
                if records
            ]

        return [
            (
                {
                    "text": RAGFlowPdfParser.remove_tag("".join(record["text"] + "\n" for record in records)),
                    "doc_type_kwd": "text",
                    PDF_POSITIONS_KEY: merge_pdf_positions(records),
                }
                if records[0]["doc_type_kwd"] == "text"
                else {
                    "text": records[0]["text"],
                    "doc_type_kwd": records[0]["doc_type_kwd"],
                    "img_id": records[0]["img_id"],
                    PDF_POSITIONS_KEY: records[0][PDF_POSITIONS_KEY],
                }
            )
            for records in record_groups
            if records
        ]