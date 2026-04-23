def _iter_paragraph_inner_content(
        self,
        paragraph: Paragraph,
        container: Optional[BaseOxmlElement] = None,
    ) -> Iterator[Union[Run, Hyperlink]]:
        """Yield visible paragraph inline containers in document order.

        python-docx only walks direct ``w:r`` and ``w:hyperlink`` children of ``w:p``.
        Inline ``w:sdt`` content controls are skipped entirely, which drops their text
        from both ``paragraph.text`` and ``paragraph.iter_inner_content()``. This walker
        treats ``w:sdt`` and a few transparent wrapper nodes as pass-through containers
        and reuses the existing Run/Hyperlink wrappers for the actual visible content.
        """
        if container is None:
            container = paragraph._element

        _W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

        for child in container:
            tag_name = etree.QName(child).localname

            if tag_name == "r":
                yield Run(child, paragraph)
            elif tag_name == "hyperlink":
                yield Hyperlink(child, paragraph)
            elif tag_name == "sdt":
                sdt_content = child.find(f"{{{_W_NS}}}sdtContent")
                if sdt_content is not None:
                    yield from self._iter_paragraph_inner_content(paragraph, sdt_content)
            elif tag_name in self._PARAGRAPH_TRANSPARENT_INLINE_CONTAINERS:
                yield from self._iter_paragraph_inner_content(paragraph, child)