def _process_sitemap_element(
        self, elem: lxml.etree._Element
    ) -> dict[str, Any] | None:
        d: dict[str, Any] = {}
        alternate: list[str] = []
        has_loc = False

        for el in elem:
            try:
                tag_name = self._get_tag_name(el)
                if not tag_name:
                    continue

                if tag_name == "link":
                    if href := el.get("href"):
                        alternate.append(href)
                else:
                    d[tag_name] = el.text.strip() if el.text else ""
                    if not has_loc and tag_name == "loc":
                        has_loc = True
            finally:
                el.clear()
        elem.clear()
        parent = elem.getparent()
        if parent is not None:
            while elem.getprevious() is not None:
                del parent[0]

        if not has_loc:
            return None

        if alternate:
            d["alternate"] = alternate

        return d