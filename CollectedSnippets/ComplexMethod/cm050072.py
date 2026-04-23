def add_invoice_line_optional_nodes(self, line_node, vals, optional_line_fields):
        base_line = vals['base_line']
        record = base_line['record']
        if not isinstance(record, models.Model) or record._name != 'account.move.line':
            return

        move_line_optional_fields = {
            key: record[key]
            for key in record._fields
            if (
                key.startswith("x_studio_peppol")
                and record[key]
                and key in optional_line_fields
            )
        }
        for field in move_line_optional_fields:
            node = line_node
            for tag in optional_line_fields[field]["path"]:
                if tag not in node:
                    node[tag] = {}
                node = node[tag]
            node.update(optional_line_fields[field]["attrs"](record))