def _get_label_from_elements(elements: Iterable[lxml.etree._Element], image_prefix: str = "[media] ") -> str:
    """Return the first label that can be extracted from a collection of elements"""
    for element in elements:
        if element.tag == "img":
            if img_alt := element.get("alt"):
                return f"{image_prefix}{img_alt}"
            if img_src := element.get("src"):
                img_src_tail = img_src.split("/")[-1]
                return f"{image_prefix}{img_src_tail}"
            return ""
        if isinstance(element, lxml.html.HtmlComment):  # A known "hack"
            continue
        if element.tag == "p" and element.get("class") == "o_outlook_hack":
            children = element.getchildren()
            if label := _get_label_from_elements(children):
                return label
    return ""