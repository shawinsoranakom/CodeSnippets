def _transfer_to_tables(self, doc):
        tables = []
        for tab in getattr(doc, "tables", []):
            img = None
            positions = ""
            bbox = _extract_bbox_from_prov(tab)
            if bbox:
                img, positions = self.cropout_docling_table(bbox.page_no, (bbox.x0, bbox.y0, bbox.x1, bbox.y1))
            html = ""
            try:
                html = tab.export_to_html(doc=doc)
            except Exception:
                pass
            tables.append(((img, html), positions if positions else ""))
        for pic in getattr(doc, "pictures", []):
            img = None
            positions = ""
            bbox = _extract_bbox_from_prov(pic)
            if bbox:
                img, positions = self.cropout_docling_table(bbox.page_no, (bbox.x0, bbox.y0, bbox.x1, bbox.y1))
            captions = ""
            try:
                captions = pic.caption_text(doc=doc)
            except Exception:
                pass
            tables.append(((img, [captions]), positions if positions else ""))
        return tables