def test_computed_fields_without_dependencies(self):
        for model in self.env.values():
            if model._abstract or not model._auto:
                continue

            for field in model._fields.values():
                if str(field) in IGNORE_COMPUTED_FIELDS:
                    continue
                if not field.compute or self.registry.field_depends[field]:
                    continue
                # ignore if the field does not appear in a form view
                domain = [
                    ('model', '=', model._name),
                    ('type', '=', 'form'),
                    ('arch_db', 'like', field.name),
                ]
                if not self.env['ir.ui.view'].search_count(domain, limit=1):
                    continue

                with self.subTest(msg=f"Compute method of {field} should work on new record."):
                    with self.env.cr.savepoint():
                        model.new()[field.name]