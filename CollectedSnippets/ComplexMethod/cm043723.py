def _parse_page(html: str) -> list[dict[str, Any]]:
    sec = re.search(
        r'<ol[^>]*class="[^"]*results[^"]*"[^>]*>(.*?)</ol>', html, re.DOTALL
    )
    if not sec:
        return []

    raw_items = re.findall(r"<li[^>]*>(.*?)</li>", sec.group(1), re.DOTALL)
    results: list[dict[str, Any]] = []

    for item in raw_items[::2]:
        vi = re.search(r'class="visualIndicator">([^<]+)<', item)
        if not vi:
            continue
        doc_type = vi.group(1).strip()

        href_m = re.search(r'class="result-heading".*?href="(/[^"?]+)', item, re.DOTALL)
        url = f"https://www.congress.gov{href_m.group(1)}" if href_m else ""
        if not url:
            continue

        heading_m = re.search(r'class="result-heading">(.*?)</span>', item, re.DOTALL)
        heading = (
            _decode(re.sub(r"<[^>]+>", " ", heading_m.group(1))) if heading_m else ""
        )

        title_m = re.search(r'class="result-title">(.*?)</span>', item, re.DOTALL)
        title = _decode(re.sub(r"<[^>]+>", " ", title_m.group(1))) if title_m else ""

        doc: dict[str, Any] = {
            "type": doc_type,
            "url": url,
            "heading": heading,
        }
        if title:
            doc["title"] = title

        for span in re.findall(r'class="result-item">(.*?)</span>', item, re.DOTALL):
            key_m = re.search(r"<strong>([^<]+):</strong>(.*)", span, re.DOTALL)
            if key_m:
                key = key_m.group(1).strip()
                val = _decode(re.sub(r"<[^>]+>", " ", key_m.group(2)))
                doc[key] = val
            else:
                text = _decode(re.sub(r"<[^>]+>", " ", span))
                if text:
                    doc.setdefault("date", text)

        results.append(doc)

    return results