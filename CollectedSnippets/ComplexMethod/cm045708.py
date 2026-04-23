async def parse(self, contents: bytes) -> list[tuple[str, dict]]:

        with optional_imports("xpack-llm-docs"):
            from docling_core.transforms.chunker.hierarchical_chunker import BaseChunk
            from docling_core.types.doc.document import PictureItem, TableItem
            from docling_core.types.doc.labels import DocItemLabel
            from docling_core.types.io import DocumentStream

        stream = DocumentStream(name="document.pdf", stream=BytesIO(contents))

        # parse document
        parsing_result = self.converter.convert(stream)
        doc = parsing_result.document

        # analyze images and/or tables with multimodal llm
        if self.multimodal_llm:
            if self.image_parsing_strategy == "llm":
                picture_items: list[PictureItem] = []
                b64_picture_imgs = []
                # collect all docling items that are pictures and their base64 encoded images
                for item, _ in doc.iterate_items():
                    if isinstance(item, PictureItem):
                        if item.image is not None:
                            b64_picture_imgs.append(str(item.image.uri))
                            picture_items.append(item)
                # parse all images in one batch
                picture_descriptions = await self.parse_visual_data(
                    b64_picture_imgs, prompts.DEFAULT_IMAGE_PARSE_PROMPT
                )
                # modify document's items with the parsed descriptions (saved as additional captions)
                for item, description in zip(picture_items, picture_descriptions):
                    new_text_item = doc.add_text(
                        DocItemLabel.CAPTION, description, parent=item
                    )
                    item.captions.append(new_text_item.get_ref())

            if self.table_parsing_strategy == "llm":
                table_items: list[TableItem] = []
                b64_table_imgs = []
                for item, _ in doc.iterate_items():
                    if isinstance(item, TableItem):
                        if item.image is not None:
                            b64_table_imgs.append(str(item.image.uri))
                            table_items.append(item)
                table_descriptions = await self.parse_visual_data(
                    b64_table_imgs, prompts.DEFAULT_TABLE_PARSE_PROMPT
                )
                for item, description in zip(table_items, table_descriptions):
                    new_text_item = doc.add_text(
                        DocItemLabel.CAPTION, description, parent=item
                    )
                    item.captions.append(new_text_item.get_ref())

        # chunk the document
        chunks: list[tuple[str, dict]] = []
        if self.chunker:

            docling_chunks: Iterator[BaseChunk] = self.chunker.chunk(doc)
            for chunk in docling_chunks:
                md_text, meta = self.format_chunk(chunk)
                chunks.append((md_text, meta))

        # if chunking is disabled then format the document into markdown and treat it as one, large chunk
        else:
            md_text, meta = self.format_document(doc)
            chunks.append((md_text, meta))

        return chunks