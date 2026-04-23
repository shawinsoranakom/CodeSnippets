def _parse_head(src: str) -> Dict[str, Any]:
    if LXML:
        try:
            if isinstance(src, str):
                # strip Unicode, let lxml decode
                src = src.encode("utf-8", "replace")
            doc = lxml_html.fromstring(src)
        except (ValueError, etree.ParserError):
            return {}        # malformed, bail gracefully
        info: Dict[str, Any] = {
            "title": (doc.find(".//title").text or "").strip()
            if doc.find(".//title") is not None else None,
            "charset": None,
            "meta": {}, "link": {}, "jsonld": []
        }
        for el in doc.xpath(".//meta"):
            k = el.attrib.get("name") or el.attrib.get(
                "property") or el.attrib.get("http-equiv")
            if k:
                info["meta"][k.lower()] = el.attrib.get("content", "")
            elif "charset" in el.attrib:
                info["charset"] = el.attrib["charset"].lower()
        for el in doc.xpath(".//link"):
            rel_attr = el.attrib.get("rel", "")
            if not rel_attr:
                continue
            # Handle multiple space-separated rel values
            rel_values = rel_attr.lower().split()
            entry = {a: el.attrib[a] for a in (
                "href", "as", "type", "hreflang") if a in el.attrib}
            # Add entry for each rel value
            for rel in rel_values:
                info["link"].setdefault(rel, []).append(entry)
        # Extract JSON-LD structured data
        for script in doc.xpath('.//script[@type="application/ld+json"]'):
            if script.text:
                try:
                    jsonld_data = json.loads(script.text.strip())
                    info["jsonld"].append(jsonld_data)
                except json.JSONDecodeError:
                    pass
        # Extract html lang attribute
        html_elem = doc.find(".//html")
        if html_elem is not None:
            info["lang"] = html_elem.attrib.get("lang", "")
        return info
    # regex fallback
    info: Dict[str, Any] = {"title": None, "charset": None,
                            "meta": {}, "link": {}, "jsonld": [], "lang": ""}
    m = _title_rx.search(src)
    info["title"] = m.group(1).strip() if m else None
    for k, v in _meta_rx.findall(src):
        info["meta"][k.lower()] = v
    m = _charset_rx.search(src)
    info["charset"] = m.group(1).lower() if m else None
    for rel, href in _link_rx.findall(src):
        info["link"].setdefault(rel.lower(), []).append({"href": href})
    # Try to extract JSON-LD with regex
    jsonld_pattern = re.compile(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
    for match in jsonld_pattern.findall(src):
        try:
            jsonld_data = json.loads(match.strip())
            info["jsonld"].append(jsonld_data)
        except json.JSONDecodeError:
            pass
    # Try to extract lang attribute
    lang_match = re.search(r'<html[^>]*lang=["\']?([^"\' >]+)', src, re.I)
    if lang_match:
        info["lang"] = lang_match.group(1)
    return info