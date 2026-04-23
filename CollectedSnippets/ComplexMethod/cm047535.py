def _update_inverses(self, records: BaseModel, value):
        """ Add `records` to the cached values of the inverse fields of `self`. """
        if not value:
            return
        model_ids = self._record_ids_per_res_model(records)

        for invf in records.pool.field_inverses[self]:
            records = records.browse(model_ids[invf.model_name])
            if not records:
                continue
            corecord = records.env[invf.model_name].browse(value)
            records = records.filtered_domain(invf.get_comodel_domain(corecord))
            if not records:
                continue
            ids0 = invf._get_cache(corecord.env).get(corecord.id)
            # if the value for the corecord is not in cache, but this is a new
            # record, assign it anyway, as you won't be able to fetch it from
            # database (see `test_sale_order`)
            if ids0 is not None or not corecord.id:
                ids1 = tuple(unique((ids0 or ()) + records._ids))
                invf._update_cache(corecord, ids1)