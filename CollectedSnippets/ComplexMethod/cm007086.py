def export_document(self) -> list[Data]:
        documents, warning = extract_docling_documents(self.data_inputs, self.doc_key)
        if warning:
            self.status = warning

        results: list[Data] = []
        try:
            image_mode = ImageRefMode(self.image_mode)
            for doc in documents:
                content = ""
                if self.export_format == "Markdown":
                    content = doc.export_to_markdown(
                        image_mode=image_mode,
                        image_placeholder=self.md_image_placeholder,
                        page_break_placeholder=self.md_page_break_placeholder,
                    )
                elif self.export_format == "HTML":
                    content = doc.export_to_html(image_mode=image_mode)
                elif self.export_format == "Plaintext":
                    content = doc.export_to_text()
                elif self.export_format == "DocTags":
                    content = doc.export_to_doctags()

                # Preserve metadata from the DoclingDocument
                metadata: dict = {"export_format": self.export_format}
                if hasattr(doc, "name") and doc.name:
                    metadata["name"] = doc.name
                if hasattr(doc, "origin") and doc.origin is not None:
                    if hasattr(doc.origin, "filename") and doc.origin.filename:
                        metadata["filename"] = doc.origin.filename
                    if hasattr(doc.origin, "binary_hash") and doc.origin.binary_hash:
                        metadata["document_id"] = str(doc.origin.binary_hash)
                    if hasattr(doc.origin, "mimetype") and doc.origin.mimetype:
                        metadata["mimetype"] = doc.origin.mimetype

                results.append(Data(text=content, data={"text": content, **metadata}))
        except Exception as e:
            msg = f"Error splitting text: {e}"
            raise TypeError(msg) from e

        return results