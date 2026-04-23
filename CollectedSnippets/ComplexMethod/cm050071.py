def add_invoice_optional_nodes(self, document_node, vals, optional_fields):
        move = vals['invoice']
        invoice_optional_fields = {key: move[key] for key in move._fields if key.startswith("x_studio_peppol") and move[key] and key in optional_fields}
        for field in invoice_optional_fields:
            path = optional_fields[field]["path"]
            attrs = optional_fields[field]["attrs"](move)
            node = document_node
            for tag in path:
                if tag not in node:
                    node[tag] = {}
                node = node[tag]
            node.update(attrs)