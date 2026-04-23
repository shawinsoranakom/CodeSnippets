def _read_group_empty_value(self, spec):
        """ Return the empty value corresponding to the given groupby spec or aggregate spec. """
        if spec == '__count':
            return 0
        fname, chain_fnames, func = parse_read_group_spec(spec)  # func is either None, granularity or an aggregate
        if func in ('count', 'count_distinct'):
            return 0
        if func in ('array_agg', 'array_agg_distinct'):
            return []
        field = self._fields[fname]
        if (not func or func == 'recordset') and (field.relational or fname == 'id'):
            if chain_fnames and field.type == 'many2one':
                groupby_seq = f"{chain_fnames}:{func}" if func else chain_fnames
                model = self.env[field.comodel_name]
                return model._read_group_empty_value(groupby_seq)
            return self.env[field.comodel_name] if field.relational else self.env[self._name]
        return False