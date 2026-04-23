def testCloneDocumentTypeDeepOk(self):
        doctype = create_nonempty_doctype()
        clone = doctype.cloneNode(1)
        self.confirm(clone is not None
                and clone.nodeName == doctype.nodeName
                and clone.name == doctype.name
                and clone.publicId == doctype.publicId
                and clone.systemId == doctype.systemId
                and len(clone.entities) == len(doctype.entities)
                and clone.entities.item(len(clone.entities)) is None
                and len(clone.notations) == len(doctype.notations)
                and clone.notations.item(len(clone.notations)) is None
                and len(clone.childNodes) == 0)
        for i in range(len(doctype.entities)):
            se = doctype.entities.item(i)
            ce = clone.entities.item(i)
            self.confirm((not se.isSameNode(ce))
                    and (not ce.isSameNode(se))
                    and ce.nodeName == se.nodeName
                    and ce.notationName == se.notationName
                    and ce.publicId == se.publicId
                    and ce.systemId == se.systemId
                    and ce.encoding == se.encoding
                    and ce.actualEncoding == se.actualEncoding
                    and ce.version == se.version)
        for i in range(len(doctype.notations)):
            sn = doctype.notations.item(i)
            cn = clone.notations.item(i)
            self.confirm((not sn.isSameNode(cn))
                    and (not cn.isSameNode(sn))
                    and cn.nodeName == sn.nodeName
                    and cn.publicId == sn.publicId
                    and cn.systemId == sn.systemId)