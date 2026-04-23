def _search(self, domain, offset=0, limit=None, order=None, *, active_test=True, bypass_access=False):
        assert not self._active_name, "active name not supported on ir.attachment"
        disable_binary_fields_attachments = False
        domain = Domain(domain)
        if (
            not self.env.context.get('skip_res_field_check')
            and not any(d.field_expr in ('id', 'res_field') for d in domain.iter_conditions())
            and not bypass_access
        ):
            disable_binary_fields_attachments = True
            domain &= Domain('res_field', '=', False)

        domain = domain.optimize(self)
        if self.env.su or bypass_access or domain.is_false():
            return super()._search(domain, offset, limit, order, active_test=active_test, bypass_access=bypass_access)

        # General access rules
        # - public == True are always accessible
        sec_domain = Domain('public', '=', True)
        # - res_id == False needs to be system user or creator
        res_ids = condition_values(self, 'res_id', domain)
        if not res_ids or False in res_ids:
            if self.env.is_system():
                sec_domain |= Domain('res_id', '=', False)
            else:
                sec_domain |= Domain('res_id', '=', False) & Domain('create_uid', '=', self.env.uid)

        # Search by res_model and res_id, filter using permissions from res_model
        # - res_id != False needs then check access on the linked res_model record
        # - res_field != False needs to check field access on the res_model
        res_model_names = condition_values(self, 'res_model', domain)
        if 0 < len(res_model_names or ()) <= 5:
            env = self.with_context(active_test=False).env
            for res_model_name in res_model_names:
                comodel = env.get(res_model_name)
                if comodel is None:
                    continue
                codomain = Domain('res_model', '=', comodel._name)
                comodel_res_ids = condition_values(self, 'res_id', domain.map_conditions(
                    lambda cond: codomain & cond if cond.field_expr == 'res_model' else cond
                ))
                query = comodel._search(Domain('id', 'in', comodel_res_ids) if comodel_res_ids else Domain.TRUE)
                if query.is_empty():
                    continue
                if query.where_clause:
                    codomain &= Domain('res_id', 'in', query)
                if not disable_binary_fields_attachments and not self.env.is_system():
                    accessible_fields = [
                        field.name
                        for field in comodel._fields.values()
                        if field.type == 'binary' or (field.relational and field.comodel_name == self._name)
                        if comodel._has_field_access(field, 'read')
                    ]
                    accessible_fields.append(False)
                    codomain &= Domain('res_field', 'in', accessible_fields)
                sec_domain |= codomain

            return super()._search(domain & sec_domain, offset, limit, order, active_test=active_test)

        # We do not have a small restriction on res_model. We still need to
        # support other queries such as: `('id', 'in' ...)`.
        # Restrict with domain and add all attachments linked to a model.
        domain &= sec_domain | Domain('res_model', '!=', False)
        domain = domain.optimize_full(self)
        ordered = bool(order)
        if limit is None:
            records = self.sudo().with_context(active_test=False).search_fetch(
                domain, SECURITY_FIELDS, order=order).sudo(False)
            return records._filtered_access('read')[offset:]._as_query(ordered)
        # Fetch by small batches
        sub_offset = 0
        limit += offset
        result = []
        if not ordered:
            # By default, order by model to batch access checks.
            order = 'res_model nulls first, id'
        while len(result) < limit:
            records = self.sudo().with_context(active_test=False).search_fetch(
                domain,
                SECURITY_FIELDS,
                offset=sub_offset,
                limit=PREFETCH_MAX,
                order=order,
            ).sudo(False)
            result.extend(records._filtered_access('read')._ids)
            if len(records) < PREFETCH_MAX:
                # There are no more records
                break
            sub_offset += PREFETCH_MAX
        return self.browse(result[offset:limit])._as_query(ordered)