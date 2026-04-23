def fill_spec(node, model, fields_spec):
            if node.tag == 'field':
                field_name = node.attrib['name']
                field_spec = fields_spec.setdefault(field_name, {})
                field = model._fields.get(field_name)
                if field is not None:
                    sub_fields_spec = {}
                    if field.type == 'many2one':
                        sub_fields_spec.setdefault('display_name', {})
                    if field.relational:
                        comodel = model.env[field.comodel_name]
                        for child in node:
                            fill_spec(child, comodel, sub_fields_spec)
                    if field.type == 'one2many':
                        sub_fields_spec.pop(field.inverse_name, None)
                    if sub_fields_spec:
                        field_spec.setdefault('fields', {}).update(sub_fields_spec)
            else:
                for child in node:
                    fill_spec(child, model, fields_spec)