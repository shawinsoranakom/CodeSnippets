def _load_pos_data_relations(self, model, fields):
        model_fields = self.env[model]._fields
        relations = {}

        for name, params in model_fields.items():
            if (name not in fields and len(fields)) or (params.manual and not len(fields)):
                continue

            if params.comodel_name:
                relations[name] = {
                    'name': name,
                    'model': params.model_name,
                    'compute': bool(params.compute),
                    'related': bool(params.related),
                    'relation': params.comodel_name,
                    'type': params.type,
                }
                if params.type == 'many2one' and params.ondelete:
                    relations[name]['ondelete'] = params.ondelete
                if params.type == 'one2many' and params.inverse_name:
                    relations[name]['inverse_name'] = params.inverse_name
                if params.type == 'many2many':
                    relations[name]['relation_table'] = self.env[model]._fields[name].relation
            else:
                relations[name] = {
                    'name': name,
                    'type': params.type,
                    'compute': bool(params.compute),
                    'related': bool(params.related),
                }

        return relations