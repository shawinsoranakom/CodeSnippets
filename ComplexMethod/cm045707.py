def format_document(self, doc: DoclingDocument) -> tuple[str, dict]:
        from docling_core.types.doc.document import PictureItem, TableItem, TextItem
        from docling_core.types.doc.labels import DocItemLabel

        text = ""

        for item, level in doc.iterate_items():

            if isinstance(item, TextItem):
                label: DocItemLabel = item.label

                if label in [
                    DocItemLabel.CAPTION,
                    DocItemLabel.PAGE_FOOTER,
                    DocItemLabel.FOOTNOTE,
                ]:
                    continue

                if label == DocItemLabel.TITLE:
                    text += "# "
                if label == DocItemLabel.SECTION_HEADER:
                    text += "#" * (level + 1) + " "

                text += item.text

            elif isinstance(item, TableItem):
                table_df = item.export_to_dataframe()
                text += table_df.to_markdown(index=False)
                captions = [c.text for c in [r.resolve(doc) for r in item.captions]]
                if len(captions):
                    text += "\n\n" + "\n\n".join(captions)

            elif isinstance(item, PictureItem):
                captions = [cap.resolve(doc).text for cap in item.captions]
                if len(captions):
                    text += "\n\n".join(captions)

            else:
                continue

            text += "\n\n"

        return (text, {})