def _get_translatable_records(self, imd_records):
        """ Filter the records that are translatable

        A record is considered as untranslatable if:
        - it does not exist
        - the model is flagged with _translate=False
        - it is a field of a model flagged with _translate=False
        - it is a selection of a field of a model flagged with _translate=False

        :param records: a list of namedtuple ImdInfo belonging to the same model
        """
        model = next(iter(imd_records)).model
        if model not in self.env:
            _logger.error("Unable to find object %r", model)
            return self.env["_unknown"].browse()

        if not self.env[model]._translate:
            return self.env[model].browse()

        res_ids = [r.res_id for r in imd_records]
        records = self.env[model].browse(res_ids).exists()
        if len(records) < len(res_ids):
            missing_ids = set(res_ids) - set(records.ids)
            missing_records = [f"{r.module}.{r.name}" for r in imd_records if r.res_id in missing_ids]
            _logger.warning("Unable to find records of type %r with external ids %s", model, ', '.join(missing_records))
            if not records:
                return records

        if model == 'ir.model.fields.selection':
            fields = defaultdict(list)
            for selection in records:
                fields[selection.field_id] = selection
            for field, selection in fields.items():
                field_name = field.name
                field_model = self.env.get(field.model)
                if (field_model is None or not field_model._translate or
                        field_name not in field_model._fields):
                    # the selection is linked to a model with _translate=False, remove it
                    records -= selection
        elif model == 'ir.model.fields':
            for field in records:
                field_name = field.name
                field_model = self.env.get(field.model)
                if (field_model is None or not field_model._translate or
                        field_name not in field_model._fields):
                    # the field is linked to a model with _translate=False, remove it
                    records -= field

        return records