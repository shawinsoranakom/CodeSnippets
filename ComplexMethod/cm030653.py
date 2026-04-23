def testNormalizeDeleteWithTwoNonTextSiblings(self):
        doc = parseString("<doc/>")
        root = doc.documentElement
        root.appendChild(doc.createElement("i"))
        root.appendChild(doc.createTextNode(""))
        root.appendChild(doc.createElement("i"))
        self.confirm(len(root.childNodes) == 3
                and root.childNodes.length == 3,
                "testNormalizeDeleteWithTwoSiblings -- preparation")
        doc.normalize()
        self.confirm(len(root.childNodes) == 2
                and root.childNodes.length == 2
                and root.firstChild is not root.lastChild
                and root.firstChild.nextSibling is root.lastChild
                and root.firstChild.previousSibling is None
                and root.lastChild.previousSibling is root.firstChild
                and root.lastChild.nextSibling is None
                , "testNormalizeDeleteWithTwoSiblings -- result")
        doc.unlink()