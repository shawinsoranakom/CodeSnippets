def _get_form(
    response: TextResponse,
    formname: str | None,
    formid: str | None,
    formnumber: int,
    formxpath: str | None,
) -> FormElement:
    """Find the wanted form element within the given response."""
    root = response.selector.root
    forms = root.xpath("//form")
    if not forms:
        raise ValueError(f"No <form> element found in {response}")

    if formname is not None:
        f = root.xpath(f'//form[@name="{formname}"]')
        if f:
            return cast("FormElement", f[0])

    if formid is not None:
        f = root.xpath(f'//form[@id="{formid}"]')
        if f:
            return cast("FormElement", f[0])

    # Get form element from xpath, if not found, go up
    if formxpath is not None:
        nodes = root.xpath(formxpath)
        if nodes:
            el = nodes[0]
            while True:
                if el.tag == "form":
                    return cast("FormElement", el)
                el = el.getparent()
                if el is None:
                    break
        raise ValueError(f"No <form> element found with {formxpath}")

    # If we get here, it means that either formname was None or invalid
    try:
        form = forms[formnumber]
    except IndexError:
        raise IndexError(f"Form number {formnumber} not found in {response}") from None
    return cast("FormElement", form)