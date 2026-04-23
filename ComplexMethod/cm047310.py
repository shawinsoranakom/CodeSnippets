def _reflect_selections(self, model_names):
        """ Reflect the selections of the fields of the given models. """
        fields = [
            field
            for model_name in model_names
            for field_name, field in self.env[model_name]._fields.items()
            if field.type in ('selection', 'reference')
            if isinstance(field.selection, list)
        ]
        if not fields:
            return
        if invalid_fields := OrderedSet(
            field for field in fields
            for selection in field.selection
            for value_label in selection
            if not isinstance(value_label, str)
        ):
            raise ValidationError(_("Fields %s contain a non-str value/label in selection", invalid_fields))

        # determine expected and existing rows
        IMF = self.env['ir.model.fields']
        expected = {
            (field_id, value): (label, index)
            for field in fields
            for field_id in [IMF._get_ids(field.model_name)[field.name]]
            for index, (value, label) in enumerate(field.selection)
        }

        cr = self.env.cr
        query = """
            SELECT s.field_id, s.value, s.name->>'en_US', s.sequence
            FROM ir_model_fields_selection s, ir_model_fields f
            WHERE s.field_id = f.id AND f.model IN %s
        """
        cr.execute(query, [tuple(model_names)])
        existing = {row[:2]: row[2:] for row in cr.fetchall()}

        # create or update rows
        cols = ['field_id', 'value', 'name', 'sequence']
        rows = [key + val for key, val in expected.items() if existing.get(key) != val]
        if rows:
            ids = upsert_en(self, cols, rows, ['field_id', 'value'])
            self.pool.post_init(mark_modified, self.browse(ids), cols[2:])

        # update their XML ids
        module = self.env.context.get('module')
        if not module:
            return

        query = """
            SELECT f.model, f.name, s.value, s.id
            FROM ir_model_fields_selection s, ir_model_fields f
            WHERE s.field_id = f.id AND f.model IN %s
        """
        cr.execute(query, [tuple(model_names)])
        selection_ids = {row[:3]: row[3] for row in cr.fetchall()}

        data_list = []
        for field in fields:
            model = self.env[field.model_name]
            for value, modules in field._selection_modules(model).items():
                for m in modules:
                    xml_id = selection_xmlid(m, field.model_name, field.name, value)
                    record = self.browse(selection_ids[field.model_name, field.name, value])
                    data_list.append({'xml_id': xml_id, 'record': record})
        self.env['ir.model.data']._update_xmlids(data_list)