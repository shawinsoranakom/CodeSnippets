def _related_field(self):
        """ Return the ``ir.model.fields`` record corresponding to ``self.related``. """
        names = self.related.split(".")
        last = len(names) - 1
        model_name = self.model or self.model_id.model
        for index, name in enumerate(names):
            field = self._get(model_name, name)
            if not field:
                raise UserError(_(
                    'Unknown field name "%(field_name)s" in related field "%(related_field)s"',
                    field_name=name,
                    related_field=self.related,
                ))
            model_name = field.relation
            if index < last and not field.relation:
                raise UserError(_(
                    'Non-relational field name "%(field_name)s" in related field "%(related_field)s"',
                    field_name=name,
                    related_field=self.related,
                ))
            if not field.store and index < last:
                raise UserError(_(
                    'Field "%(field_name)s" in related path "%(related_field)s" is not stored. '
                    'Non-stored fields cannot be used in related fields.',
                    field_name=name,
                    related_field=self.related,
                ))
        return field