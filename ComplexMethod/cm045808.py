def _resolve_hyperlink_from_run(self, run, shape) -> Optional[str]:
        """解析 run 对应的超链接，优先公开 API，回退到 XML + rels。"""
        try:
            if hasattr(run, "hyperlink") and run.hyperlink is not None:
                address = run.hyperlink.address
                if address and str(address).strip():
                    return str(address).strip()
        except Exception:
            pass

        try:
            rPr = run._r.find("a:rPr", namespaces=self.namespaces)
            if rPr is None:
                return None

            hlink_click = rPr.find("a:hlinkClick", namespaces=self.namespaces)
            if hlink_click is None:
                return None

            rid = hlink_click.get(
                "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            )
            if not rid:
                return None

            rels = shape.part.rels
            if rid not in rels:
                return None

            rel = rels[rid]
            target_ref = getattr(rel, "target_ref", None)
            if target_ref and str(target_ref).strip():
                return str(target_ref).strip()

            target_part = getattr(rel, "target_part", None)
            if target_part is not None:
                partname = getattr(target_part, "partname", None)
                if partname and str(partname).strip():
                    return str(partname).strip()
        except Exception:
            return None

        return None