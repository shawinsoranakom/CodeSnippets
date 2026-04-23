def testRenameElement(self):
        doc = parseString("<doc/>")
        elem = doc.documentElement

        # Simple renaming
        elem = doc.renameNode(elem, xml.dom.EMPTY_NAMESPACE, "a")
        self.confirm(elem.tagName == "a"
                and elem.nodeName == "a"
                and elem.localName is None
                and elem.namespaceURI == xml.dom.EMPTY_NAMESPACE
                and elem.prefix is None
                and elem.ownerDocument.isSameNode(doc))

        # Rename to have a namespace, no prefix
        elem = doc.renameNode(elem, "http://xml.python.org/ns", "b")
        self.confirm(elem.tagName == "b"
                and elem.nodeName == "b"
                and elem.localName == "b"
                and elem.namespaceURI == "http://xml.python.org/ns"
                and elem.prefix is None
                and elem.ownerDocument.isSameNode(doc))

        # Rename to have a namespace, with prefix
        elem = doc.renameNode(elem, "http://xml.python.org/ns2", "p:c")
        self.confirm(elem.tagName == "p:c"
                and elem.nodeName == "p:c"
                and elem.localName == "c"
                and elem.namespaceURI == "http://xml.python.org/ns2"
                and elem.prefix == "p"
                and elem.ownerDocument.isSameNode(doc))

        # Rename back to a simple non-NS node
        elem = doc.renameNode(elem, xml.dom.EMPTY_NAMESPACE, "d")
        self.confirm(elem.tagName == "d"
                and elem.nodeName == "d"
                and elem.localName is None
                and elem.namespaceURI == xml.dom.EMPTY_NAMESPACE
                and elem.prefix is None
                and elem.ownerDocument.isSameNode(doc))

        self.checkRenameNodeSharedConstraints(doc, elem)
        doc.unlink()