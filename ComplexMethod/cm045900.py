def _extract_paragraph_bookmark(self, paragraph_element: BaseOxmlElement) -> Optional[str]:
        """Extract a bookmark name from a paragraph, prioritizing TOC bookmarks."""
        bookmark_name_attr = (
            "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name"
        )
        names = []
        for bm in paragraph_element.findall(
            ".//w:bookmarkStart", namespaces=DocxConverter._BLIP_NAMESPACES
        ):
            name = bm.get(bookmark_name_attr, "").strip()
            if not name:
                continue
            # skip Word navigation artifacts
            if name.startswith("_GoBack"):
                continue
            names.append(name)
        if not names:
            return None
        toc_names = [name for name in names if name.startswith("_Toc")]
        if toc_names:
            # Prefer anchors that are actually referenced by TOC hyperlinks.
            for name in toc_names:
                if name in self.toc_anchor_set:
                    return name
            return toc_names[0]
        return names[0]