def testRenameAttribute(self):
        doc = parseString("<doc a='v'/>")
        elem = doc.documentElement
        attrmap = elem.attributes
        attr = elem.attributes['a']

        # Simple renaming
        attr = doc.renameNode(attr, xml.dom.EMPTY_NAMESPACE, "b")
        self.confirm(attr.name == "b"
                and attr.nodeName == "b"
                and attr.localName is None
                and attr.namespaceURI == xml.dom.EMPTY_NAMESPACE
                and attr.prefix is None
                and attr.value == "v"
                and elem.getAttributeNode("a") is None
                and elem.getAttributeNode("b").isSameNode(attr)
                and attrmap["b"].isSameNode(attr)
                and attr.ownerDocument.isSameNode(doc)
                and attr.ownerElement.isSameNode(elem))

        # Rename to have a namespace, no prefix
        attr = doc.renameNode(attr, "http://xml.python.org/ns", "c")
        self.confirm(attr.name == "c"
                and attr.nodeName == "c"
                and attr.localName == "c"
                and attr.namespaceURI == "http://xml.python.org/ns"
                and attr.prefix is None
                and attr.value == "v"
                and elem.getAttributeNode("a") is None
                and elem.getAttributeNode("b") is None
                and elem.getAttributeNode("c").isSameNode(attr)
                and elem.getAttributeNodeNS(
                    "http://xml.python.org/ns", "c").isSameNode(attr)
                and attrmap["c"].isSameNode(attr)
                and attrmap[("http://xml.python.org/ns", "c")].isSameNode(attr))

        # Rename to have a namespace, with prefix
        attr = doc.renameNode(attr, "http://xml.python.org/ns2", "p:d")
        self.confirm(attr.name == "p:d"
                and attr.nodeName == "p:d"
                and attr.localName == "d"
                and attr.namespaceURI == "http://xml.python.org/ns2"
                and attr.prefix == "p"
                and attr.value == "v"
                and elem.getAttributeNode("a") is None
                and elem.getAttributeNode("b") is None
                and elem.getAttributeNode("c") is None
                and elem.getAttributeNodeNS(
                    "http://xml.python.org/ns", "c") is None
                and elem.getAttributeNode("p:d").isSameNode(attr)
                and elem.getAttributeNodeNS(
                    "http://xml.python.org/ns2", "d").isSameNode(attr)
                and attrmap["p:d"].isSameNode(attr)
                and attrmap[("http://xml.python.org/ns2", "d")].isSameNode(attr))

        # Rename back to a simple non-NS node
        attr = doc.renameNode(attr, xml.dom.EMPTY_NAMESPACE, "e")
        self.confirm(attr.name == "e"
                and attr.nodeName == "e"
                and attr.localName is None
                and attr.namespaceURI == xml.dom.EMPTY_NAMESPACE
                and attr.prefix is None
                and attr.value == "v"
                and elem.getAttributeNode("a") is None
                and elem.getAttributeNode("b") is None
                and elem.getAttributeNode("c") is None
                and elem.getAttributeNode("p:d") is None
                and elem.getAttributeNodeNS(
                    "http://xml.python.org/ns", "c") is None
                and elem.getAttributeNode("e").isSameNode(attr)
                and attrmap["e"].isSameNode(attr))

        self.assertRaises(xml.dom.NamespaceErr, doc.renameNode, attr,
                          "http://xml.python.org/ns", "xmlns")
        self.checkRenameNodeSharedConstraints(doc, attr)
        doc.unlink()