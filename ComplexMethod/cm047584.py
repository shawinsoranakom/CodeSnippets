def _add_precomputed_values(self, vals_list: list[ValuesType]) -> None:
        """ Add missing precomputed fields to ``vals_list`` values.
        Only applies for precompute=True fields.
        """
        precomputable = {
            fname: field
            for fname, field in self._fields.items()
            if field.precompute
        }
        if not precomputable:
            return

        # determine which vals must be completed
        vals_list_todo = [
            vals
            for vals in vals_list
            if any(fname not in vals for fname in precomputable)
        ]
        if not vals_list_todo:
            return

        # create new records for the vals that must be completed
        records = self.browse().concat(*(self.new(vals) for vals in vals_list_todo))

        for record, vals in zip(records, vals_list_todo):
            vals['__precomputed__'] = precomputed = set()
            for fname, field in precomputable.items():
                if fname not in vals:
                    # computed stored fields with a column
                    # have to be computed before create
                    # s.t. required and constraints can be applied on those fields.
                    vals[fname] = field.convert_to_write(record[fname], self)
                    precomputed.add(field)