def _search_audit_log_related_record_id(self, model, operator, value):
        if (
            operator in ('like', 'ilike', 'not ilike', 'not like') and isinstance(value, str)
        ) or (
            operator in ('in', 'not in') and any(isinstance(v, str) for v in value)
        ):
            res_id_domain = [('res_id', 'in', self.env[model]._search([('display_name', operator, value)]))]
        elif operator in ('any', 'not any', 'any!', 'not any!'):
            if isinstance(value, Domain):
                query = self.env[model]._search(value)
            else:
                query = value
            res_id_domain = [('res_id', 'in' if operator in ('any', 'any!') else 'not in', query)]
        elif operator in ('in', 'not in'):
            res_id_domain = [('res_id', operator, value)]
        else:
            return NotImplemented
        return [('model', '=', model)] + res_id_domain