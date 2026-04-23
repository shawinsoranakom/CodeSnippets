def replaceChild(self, newChild, oldChild):
        if newChild.nodeType == self.DOCUMENT_FRAGMENT_NODE:
            refChild = oldChild.nextSibling
            self.removeChild(oldChild)
            return self.insertBefore(newChild, refChild)
        if newChild.nodeType not in self._child_node_types:
            raise xml.dom.HierarchyRequestErr(
                "%s cannot be child of %s" % (repr(newChild), repr(self)))
        if newChild is oldChild:
            return
        if newChild.parentNode is not None:
            newChild.parentNode.removeChild(newChild)
        try:
            index = self.childNodes.index(oldChild)
        except ValueError:
            raise xml.dom.NotFoundErr()
        self.childNodes[index] = newChild
        newChild.parentNode = self
        oldChild.parentNode = None
        if (newChild.nodeType in _nodeTypes_with_children
            or oldChild.nodeType in _nodeTypes_with_children):
            _clear_id_cache(self)
        newChild.nextSibling = oldChild.nextSibling
        newChild.previousSibling = oldChild.previousSibling
        oldChild.nextSibling = None
        oldChild.previousSibling = None
        if newChild.previousSibling:
            newChild.previousSibling.nextSibling = newChild
        if newChild.nextSibling:
            newChild.nextSibling.previousSibling = newChild
        return oldChild