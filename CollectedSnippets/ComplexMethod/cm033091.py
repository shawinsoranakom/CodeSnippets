def _iter_doc_items(self, doc) -> Iterable[tuple[str, Any, Optional[_BBox]]]:
        for t in getattr(doc, "texts", []):
            parent = getattr(t, "parent", "")
            ref = getattr(parent, "cref", "")
            label = getattr(t, "label", "")
            if (label in ("section_header", "text") and ref in ("#/body",)) or label in ("list_item",):
                text = getattr(t, "text", "") or ""
                bbox = _extract_bbox_from_prov(t)
                yield (DoclingContentType.TEXT.value, text, bbox)

        for item in getattr(doc, "texts", []):
            if getattr(item, "label", "") in ("FORMULA",):
                text = getattr(item, "text", "") or ""
                bbox = _extract_bbox_from_prov(item)
                yield (DoclingContentType.EQUATION.value, text, bbox)