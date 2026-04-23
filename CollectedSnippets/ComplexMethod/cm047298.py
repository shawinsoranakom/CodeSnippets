def _reflect_models(self, model_names):
        """ Reflect the given models. """
        # determine expected and existing rows
        rows = [
            self._reflect_model_params(self.env[model_name])
            for model_name in model_names
        ]
        cols = list(unique(['model'] + list(rows[0])))
        expected = [tuple(row[col] for col in cols) for row in rows]

        model_ids = {}
        existing = {}
        for row in select_en(self, ['id'] + cols, model_names):
            model_ids[row[1]] = row[0]
            existing[row[1]] = row[1:]

        # create or update rows
        rows = [row for row in expected if existing.get(row[0]) != row]
        if rows:
            ids = upsert_en(self, cols, rows, ['model'])
            for row, id_ in zip(rows, ids):
                model_ids[row[0]] = id_
            self.pool.post_init(mark_modified, self.browse(ids), cols[1:])

        # update their XML id
        module = self.env.context.get('module')
        if not module:
            return

        data_list = []
        for model_name, model_id in model_ids.items():
            model = self.env[model_name]
            if model._module == module:
                # model._module is the name of the module that last extended model
                xml_id = model_xmlid(module, model_name)
                record = self.browse(model_id)
                data_list.append({'xml_id': xml_id, 'record': record})
        self.env['ir.model.data']._update_xmlids(data_list)