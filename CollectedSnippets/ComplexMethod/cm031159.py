def normalize(self):
        L = []
        for child in self.childNodes:
            if child.nodeType == Node.TEXT_NODE:
                if not child.data:
                    # empty text node; discard
                    if L:
                        L[-1].nextSibling = child.nextSibling
                    if child.nextSibling:
                        child.nextSibling.previousSibling = child.previousSibling
                    child.unlink()
                elif L and L[-1].nodeType == child.nodeType:
                    # collapse text node
                    node = L[-1]
                    node.data = node.data + child.data
                    node.nextSibling = child.nextSibling
                    if child.nextSibling:
                        child.nextSibling.previousSibling = node
                    child.unlink()
                else:
                    L.append(child)
            else:
                L.append(child)
                if child.nodeType == Node.ELEMENT_NODE:
                    child.normalize()
        self.childNodes[:] = L