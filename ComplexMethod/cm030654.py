def testNormalizeRecursion(self):
        doc = parseString("<doc>"
                            "<o>"
                              "<i/>"
                              "t"
                              #
                              #x
                            "</o>"
                            "<o>"
                              "<o>"
                                "t2"
                                #x2
                              "</o>"
                              "t3"
                              #x3
                            "</o>"
                            #
                          "</doc>")
        root = doc.documentElement
        root.childNodes[0].appendChild(doc.createTextNode(""))
        root.childNodes[0].appendChild(doc.createTextNode("x"))
        root.childNodes[1].childNodes[0].appendChild(doc.createTextNode("x2"))
        root.childNodes[1].appendChild(doc.createTextNode("x3"))
        root.appendChild(doc.createTextNode(""))
        self.confirm(len(root.childNodes) == 3
                and root.childNodes.length == 3
                and len(root.childNodes[0].childNodes) == 4
                and root.childNodes[0].childNodes.length == 4
                and len(root.childNodes[1].childNodes) == 3
                and root.childNodes[1].childNodes.length == 3
                and len(root.childNodes[1].childNodes[0].childNodes) == 2
                and root.childNodes[1].childNodes[0].childNodes.length == 2
                , "testNormalize2 -- preparation")
        doc.normalize()
        self.confirm(len(root.childNodes) == 2
                and root.childNodes.length == 2
                and len(root.childNodes[0].childNodes) == 2
                and root.childNodes[0].childNodes.length == 2
                and len(root.childNodes[1].childNodes) == 2
                and root.childNodes[1].childNodes.length == 2
                and len(root.childNodes[1].childNodes[0].childNodes) == 1
                and root.childNodes[1].childNodes[0].childNodes.length == 1
                , "testNormalize2 -- childNodes lengths")
        self.confirm(root.childNodes[0].childNodes[1].data == "tx"
                and root.childNodes[1].childNodes[0].childNodes[0].data == "t2x2"
                and root.childNodes[1].childNodes[1].data == "t3x3"
                , "testNormalize2 -- joined text fields")
        self.confirm(root.childNodes[0].childNodes[1].nextSibling is None
                and root.childNodes[0].childNodes[1].previousSibling
                        is root.childNodes[0].childNodes[0]
                and root.childNodes[0].childNodes[0].previousSibling is None
                and root.childNodes[0].childNodes[0].nextSibling
                        is root.childNodes[0].childNodes[1]
                and root.childNodes[1].childNodes[1].nextSibling is None
                and root.childNodes[1].childNodes[1].previousSibling
                        is root.childNodes[1].childNodes[0]
                and root.childNodes[1].childNodes[0].previousSibling is None
                and root.childNodes[1].childNodes[0].nextSibling
                        is root.childNodes[1].childNodes[1]
                , "testNormalize2 -- sibling pointers")
        doc.unlink()