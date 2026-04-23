def getInnerText(node):
    return "".join(
        [child.data for child in node.childNodes if check_element_type(child)]
    )