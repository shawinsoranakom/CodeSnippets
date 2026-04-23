def chunk(self, dl_doc: DoclingDocument, **kwargs: Any) -> Iterator[DocChunk]:
        r"""Chunk the provided document.

        Args:
            dl_doc (DLDocument): document to chunk

        Yields:
            Iterator[Chunk]: iterator over extracted chunks
        """
        heading_by_level: dict[LevelNumber, str] = {}
        list_items: list[TextItem] = []
        for item, level in dl_doc.iterate_items():
            captions = None
            if isinstance(item, DocItem):

                # first handle any merging needed
                if self.merge_list_items:
                    if isinstance(
                        item, ListItem
                    ) or (  # TODO remove when all captured as ListItem:
                        isinstance(item, TextItem)
                        and item.label == DocItemLabel.LIST_ITEM  # type: ignore
                    ):
                        list_items.append(item)
                        continue
                    elif list_items:  # need to yield
                        yield DocChunk(
                            text=self.delim.join([i.text for i in list_items]),
                            meta=DocMeta(
                                doc_items=list_items,  # type: ignore
                                headings=[
                                    heading_by_level[k]
                                    for k in sorted(heading_by_level)
                                ]
                                or None,
                                origin=dl_doc.origin,
                            ),
                        )
                        list_items = []  # reset

                if isinstance(item, (SectionHeaderItem, TitleItem)) or (
                    isinstance(item, TextItem)
                    and item.label in [DocItemLabel.SECTION_HEADER, DocItemLabel.TITLE]
                ):
                    label: DocItemLabel = item.label
                    level = (
                        item.level
                        if isinstance(item, SectionHeaderItem)
                        else (0 if label == DocItemLabel.TITLE else 1)
                    )
                    heading_by_level[level] = item.text

                    # remove headings of higher level as they just went out of scope
                    keys_to_del = [k for k in heading_by_level if k > level]
                    for k in keys_to_del:
                        heading_by_level.pop(k, None)
                    continue

                if (
                    isinstance(item, TextItem)
                    or ((not self.merge_list_items) and isinstance(item, ListItem))
                    or isinstance(item, CodeItem)
                ):
                    # we skip captions as they are handled separately by their parents
                    # we also skip other smaller elements like page footers, footnotes etc. (TBD)
                    if item.label in ["caption", "page_footer", "footnote"]:
                        continue
                    text = item.text
                # these two following elifs are Pathway custom behavior
                elif isinstance(item, TableItem):
                    table_df = item.export_to_dataframe()
                    text = table_df.to_markdown(index=False)
                    captions = [
                        c.text for c in [r.resolve(dl_doc) for r in item.captions]
                    ] or None
                elif isinstance(item, PictureItem):
                    text = ""
                    captions = [
                        cap.resolve(dl_doc).text for cap in item.captions
                    ] or None

                else:
                    continue
                c = DocChunk(
                    text=text,
                    meta=DocMeta(
                        doc_items=[item],
                        headings=[heading_by_level[k] for k in sorted(heading_by_level)]
                        or None,
                        captions=captions,
                        origin=dl_doc.origin,
                    ),
                )
                yield c

        if self.merge_list_items and list_items:  # need to yield
            yield DocChunk(
                text=self.delim.join([i.text for i in list_items]),
                meta=DocMeta(
                    doc_items=list_items,  # type: ignore
                    headings=[heading_by_level[k] for k in sorted(heading_by_level)]
                    or None,
                    origin=dl_doc.origin,
                ),
            )