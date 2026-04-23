def _search_get_indirect_fields(self, fields, model):
        """
        Returns the list of indirect fields amongst the requested fields.

        :param fields: list of field names to be searched
        :param model: model within which to search
        :return: dict of indirect field details per indirect field name
        """
        # Are considered valid indirect fields, fields that belong to the
        # comodel behind a relational direct field.
        indirect_fields = {}
        for field in fields:
            field_parts = field.split('.')
            if len(field_parts) != 2:
                continue
            direct, indirect = field_parts
            if direct not in model._fields:
                continue
            direct_field = model._fields[direct]
            comodel_name = direct_field.comodel_name
            if comodel_name not in self.env:
                continue
            comodel_fields = self.env[comodel_name]._fields
            cofield = None
            if '_description_relation_field' in dir(direct_field):
                # One2many field's comodel reference to the model's id.
                cofield = direct_field._description_relation_field
                if cofield not in comodel_fields:
                    continue
            if indirect in comodel_fields:
                indirect_fields[field] = {
                    'direct': direct,
                    'indirect': indirect,
                    'comodel': self.env[comodel_name],
                    'cofield': cofield,
                }
        return indirect_fields