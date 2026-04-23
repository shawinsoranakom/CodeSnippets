def testSetIdAttributeNS(self):
        NS1 = "http://xml.python.org/ns1"
        NS2 = "http://xml.python.org/ns2"
        doc = parseString("<doc"
                          " xmlns:ns1='" + NS1 + "'"
                          " xmlns:ns2='" + NS2 + "'"
                          " ns1:a1='v' ns2:a2='w'/>")
        e = doc.documentElement
        a1 = e.getAttributeNodeNS(NS1, "a1")
        a2 = e.getAttributeNodeNS(NS2, "a2")
        self.confirm(doc.getElementById("v") is None
                and not a1.isId
                and not a2.isId)
        e.setIdAttributeNS(NS1, "a1")
        self.confirm(e.isSameNode(doc.getElementById("v"))
                and a1.isId
                and not a2.isId)
        e.setIdAttributeNS(NS2, "a2")
        self.confirm(e.isSameNode(doc.getElementById("v"))
                and e.isSameNode(doc.getElementById("w"))
                and a1.isId
                and a2.isId)
        # replace the a1 node; the new node should *not* be an ID
        a3 = doc.createAttributeNS(NS1, "a1")
        a3.value = "v"
        e.setAttributeNode(a3)
        self.assertTrue(e.isSameNode(doc.getElementById("w")))
        self.assertFalse(a1.isId)
        self.assertTrue(a2.isId)
        self.assertFalse(a3.isId)
        self.assertIsNone(doc.getElementById("v"))
        # renaming an attribute should not affect its ID-ness:
        doc.renameNode(a2, xml.dom.EMPTY_NAMESPACE, "an")
        self.confirm(e.isSameNode(doc.getElementById("w"))
                and a2.isId)