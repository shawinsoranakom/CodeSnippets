def children(element):
        return [c for c in element.childNodes if c.nodeType == Node.ELEMENT_NODE]