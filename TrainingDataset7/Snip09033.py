def check_element_type(element):
    if element.childNodes:
        raise SuspiciousOperation(f"Unexpected element: {element.tagName!r}")
    return element.nodeType in (element.TEXT_NODE, element.CDATA_SECTION_NODE)