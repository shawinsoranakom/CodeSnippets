def _extract_textbox_paragraphs(element) -> list:
    """Extract paragraphs from text boxes embedded in a body element.

    Text boxes appear as mc:AlternateContent > mc:Choice > wps:txbx > w:txbxContent > w:p.
    Only mc:Choice is used to avoid duplicating VML fallback content.

    Returns list of lists of w:p elements, one list per non-empty text box.
    """
    try:
        result = []
        for alt_content in element.iter(f"{_MC}AlternateContent"):
            choice = alt_content.find(f"{_MC}Choice")
            if choice is None:
                continue
            for txbx in choice.iter(f"{_WPS}txbx"):
                txbx_content = txbx.find(f"{_W}txbxContent")
                if txbx_content is None:
                    continue
                paras = txbx_content.findall(f"{_W}p")
                if not paras:
                    continue
                # Skip boxes where all paragraphs are empty
                has_text = any(
                    p.find(f".//{_W}t") is not None
                    and any(t.text for t in p.findall(f".//{_W}t") if t.text)
                    for p in paras
                )
                if has_text:
                    result.append(paras)
        return result
    except Exception:
        return []