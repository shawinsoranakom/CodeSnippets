def _get_res_ids_per_model(self, env, values_list):
        """Read everything needed in batch for the given records.

        To retrieve relational properties names, or to check their existence,
        we need to do some SQL queries. To reduce the number of queries when we read
        in batch, we prefetch everything needed before calling
        convert_to_record / convert_to_read.

        Return a dict {model: record_ids} that contains
        the existing ids for each needed models.
        """
        # ids per model we need to fetch in batch to put in cache
        ids_per_model = defaultdict(OrderedSet)

        for record_values in values_list:
            for property_definition in record_values:
                comodel = property_definition.get('comodel')
                type_ = property_definition.get('type')
                property_value = property_definition.get('value') or []
                default = property_definition.get('default') or []

                if type_ not in ('many2one', 'many2many') or comodel not in env:
                    continue

                if type_ == 'many2one':
                    default = [default] if default else []
                    property_value = [property_value] if isinstance(property_value, int) else []
                elif not is_list_of(property_value, int):
                    property_value = []

                ids_per_model[comodel].update(default)
                ids_per_model[comodel].update(property_value)

        # check existence and pre-fetch in batch
        res_ids_per_model = {}
        for model, ids in ids_per_model.items():
            recs = env[model].browse(ids).exists()
            res_ids_per_model[model] = set(recs.ids)

            for record in recs:
                # read a field to pre-fetch the recordset
                with contextlib.suppress(AccessError):
                    record.display_name

        return res_ids_per_model