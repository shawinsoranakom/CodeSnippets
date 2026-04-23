def _doc_index(self):
        modules = get_sorted_installed_modules(self.env)
        models = [
            {
                'model': ir_model.model,
                'name': ir_model.name,
                'fields': {
                    field.name: {'string': field.field_description}
                    for field in ir_model.field_id
                    # sorted(ir_model.field_id, key=partial(sort_key_field, modules, Model))
                    if field.name in Model._fields  # band-aid, see task 5172546
                    if Model._has_field_access(Model._fields[field.name], 'read')
                },
                'methods': [
                    method_name
                    for method_name in dir(Model)
                    if is_public_method(Model, method_name)
                ],
                # sorted(..., key=partial(sort_key_method, modules, type(Model))),
            }
            for ir_model in self.env['ir.model'].sudo().search([])
            if ir_model.model in self.env
            if (Model := self.env[ir_model.model]).has_access('read')
        ]
        return modules, models