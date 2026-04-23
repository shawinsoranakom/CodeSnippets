def _check_incompatible_types(self):
        incompatible_types = self._get_incompatible_types()
        if len(incompatible_types) < 2:
            return
        fields = self.env['ir.model.fields'].sudo().search_read(
            [('model', '=', 'product.template'), ('name', 'in', incompatible_types)],
            ['name', 'field_description'])
        field_descriptions = {v['name']: v['field_description'] for v in fields}
        field_list = incompatible_types + ['name']
        values = self.read(field_list)
        for val in values:
            incompatible_fields = [f for f in incompatible_types if val[f]]
            if len(incompatible_fields) > 1:
                raise ValidationError(_(
                    "The product (%(product)s) has incompatible values: %(value_list)s",
                    product=val['name'],
                    value_list=[field_descriptions[v] for v in incompatible_fields],
                ))