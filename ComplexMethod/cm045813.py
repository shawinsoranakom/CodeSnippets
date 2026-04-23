def _get_paragraph_list_info(self, shape, paragraph) -> dict:
        """基于段落->文本框->布局->母版继承链解析段落列表属性。"""
        marker_info = self._get_effective_list_marker(shape, paragraph)
        p = paragraph._element
        level = marker_info.get("level", self._get_paragraph_level(p))
        kind = marker_info.get("kind")

        if marker_info.get("is_list") is False:
            return {
                "is_list": False,
                "attribute": "unordered",
                "level": level,
                "kind": kind,
            }

        if kind == "buAutoNum":
            return {
                "is_list": True,
                "attribute": "ordered",
                "level": level,
                "kind": kind,
            }

        if kind in ("buChar", "buBlip"):
            return {
                "is_list": True,
                "attribute": "unordered",
                "level": level,
                "kind": kind,
            }

        if marker_info.get("is_list") is True:
            return {
                "is_list": True,
                "attribute": "unordered",
                "level": level,
                "kind": kind,
            }

        # 兜底：段落级标记 + 缩进层级判断
        if p.find(".//a:buAutoNum", namespaces={"a": self.namespaces["a"]}) is not None:
            return {
                "is_list": True,
                "attribute": "ordered",
                "level": paragraph.level,
                "kind": "buAutoNum",
            }

        if p.find(".//a:buChar", namespaces={"a": self.namespaces["a"]}) is not None:
            return {
                "is_list": True,
                "attribute": "unordered",
                "level": paragraph.level,
                "kind": "buChar",
            }

        if paragraph.level > 0:
            return {
                "is_list": True,
                "attribute": "unordered",
                "level": paragraph.level,
                "kind": None,
            }

        return {
            "is_list": False,
            "attribute": "unordered",
            "level": 0,
            "kind": None,
        }