def create(self, vals_list):
        # Optimisation: saving a res.config.settings even without changing any
        # values will trigger the write of all related values. This in turn may
        # trigger chain of further recomputation. To avoid it, delete values
        # that were not changed.
        for vals in vals_list:
            for field in self._fields.values():
                if not (field.name in vals and field.related and not field.readonly):
                    continue
                # we write on a related field like
                # qr_code = fields.Boolean(related='company_id.qr_code', readonly=False)
                fname0, *fnames = field.related.split(".")
                if fname0 not in vals:
                    continue

                # determine the current value
                field0 = self._fields[fname0]
                old_value = field0.convert_to_record(
                    field0.convert_to_cache(vals[fname0], self), self)
                for fname in fnames:
                    old_value = next(iter(old_value), old_value)[fname]

                # determine the new value
                new_value = field.convert_to_record(
                    field.convert_to_cache(vals[field.name], self), self)

                # drop if the value is the same
                if old_value == new_value:
                    vals.pop(field.name)

        return super().create(vals_list)