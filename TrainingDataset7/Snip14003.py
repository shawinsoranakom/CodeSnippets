def child_text(element):
        return "".join(
            c.data for c in element.childNodes if c.nodeType == Node.TEXT_NODE
        )