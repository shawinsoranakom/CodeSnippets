def testCloneDocumentTypeShallowOk(self):
        doctype = create_nonempty_doctype()
        clone = doctype.cloneNode(0)
        self.confirm(clone is not None
                and clone.nodeName == doctype.nodeName
                and clone.name == doctype.name
                and clone.publicId == doctype.publicId
                and clone.systemId == doctype.systemId
                and len(clone.entities) == 0
                and clone.entities.item(0) is None
                and len(clone.notations) == 0
                and clone.notations.item(0) is None
                and len(clone.childNodes) == 0)