def _transfer_to_sections(self, doc, parse_method: str) -> list[tuple[str, ...]]:
        sections: list[tuple[str, ...]] = []
        for typ, payload, bbox in self._iter_doc_items(doc):
            if typ == DoclingContentType.TEXT.value:
                section = payload.strip()
                if not section:
                    continue
            elif typ == DoclingContentType.EQUATION.value:
                section = payload.strip()
            else:
                continue

            tag = self._make_line_tag(bbox) if isinstance(bbox,_BBox) else ""
            if parse_method in {"manual", "pipeline"}:
                sections.append((section, typ, tag))
            elif parse_method == "paper":
                sections.append((section + tag, typ))
            else:
                sections.append((section, tag))
        return sections