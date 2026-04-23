def testSetIdAttribute(self):
        doc = parseString("<doc a1='v' a2='w'/>")
        e = doc.documentElement
        a1 = e.getAttributeNode("a1")
        a2 = e.getAttributeNode("a2")
        self.confirm(doc.getElementById("v") is None
                and not a1.isId
                and not a2.isId)
        e.setIdAttribute("a1")
        self.confirm(e.isSameNode(doc.getElementById("v"))
                and a1.isId
                and not a2.isId)
        e.setIdAttribute("a2")
        self.confirm(e.isSameNode(doc.getElementById("v"))
                and e.isSameNode(doc.getElementById("w"))
                and a1.isId
                and a2.isId)
        # replace the a1 node; the new node should *not* be an ID
        a3 = doc.createAttribute("a1")
        a3.value = "v"
        e.setAttributeNode(a3)
        self.confirm(doc.getElementById("v") is None
                and e.isSameNode(doc.getElementById("w"))
                and not a1.isId
                and a2.isId
                and not a3.isId)
        # renaming an attribute should not affect its ID-ness:
        doc.renameNode(a2, xml.dom.EMPTY_NAMESPACE, "an")
        self.confirm(e.isSameNode(doc.getElementById("w"))
                and a2.isId)