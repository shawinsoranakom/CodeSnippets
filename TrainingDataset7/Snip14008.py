def first_node(document):
        for node in document.childNodes:
            if node.nodeType not in (
                Node.COMMENT_NODE,
                Node.DOCUMENT_TYPE_NODE,
                Node.PROCESSING_INSTRUCTION_NODE,
            ):
                return node