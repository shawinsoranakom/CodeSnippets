def testNormalizeCombineAndNextSibling(self):
        doc = parseString("<doc/>")
        root = doc.documentElement
        root.appendChild(doc.createTextNode("first"))
        root.appendChild(doc.createTextNode("second"))
        root.appendChild(doc.createElement("i"))
        self.confirm(len(root.childNodes) == 3
                and root.childNodes.length == 3,
                "testNormalizeCombineAndNextSibling -- preparation")
        doc.normalize()
        self.confirm(len(root.childNodes) == 2
                and root.childNodes.length == 2
                and root.firstChild.data == "firstsecond"
                and root.firstChild is not root.lastChild
                and root.firstChild.nextSibling is root.lastChild
                and root.firstChild.previousSibling is None
                and root.lastChild.previousSibling is root.firstChild
                and root.lastChild.nextSibling is None
                , "testNormalizeCombinedAndNextSibling -- result")
        doc.unlink()