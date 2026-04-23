def _check_access(self, operation):
        """Check access for attachments.

        Rules:
        - `public` is always accessible for reading.
        - If we have `res_model and res_id`, the attachment is accessible if the
          referenced model is accessible. Also, when `res_field != False` and
          the user is not an administrator, we check the access on the field.
        - If we don't have a referenced record, the attachment is accessible to
          the administrator and the creator of the attachment.
        """
        res = super()._check_access(operation)
        remaining = self
        error_func = None
        forbidden_ids = OrderedSet()
        if res:
            forbidden, error_func = res
            if forbidden == self:
                return res
            remaining -= forbidden
            forbidden_ids.update(forbidden._ids)
        elif not self:
            return None

        if operation in ('create', 'unlink'):
            # check write operation instead of unlinking and creating for
            # related models and field access
            operation = 'write'

        # collect the records to check (by model)
        model_ids = defaultdict(set)            # {model_name: set(ids)}
        att_model_ids = []                      # [(att_id, (res_model, res_id))]
        # DLE P173: `test_01_portal_attachment`
        remaining = remaining.sudo()
        remaining.fetch(SECURITY_FIELDS)  # fetch only these fields
        for attachment in remaining:
            if attachment.public and operation == 'read':
                continue
            att_id = attachment.id
            res_model, res_id = attachment.res_model, attachment.res_id
            if not self.env.is_system():
                if not res_id and attachment.create_uid.id != self.env.uid:
                    forbidden_ids.add(att_id)
                    continue
                if res_field := attachment.res_field:
                    try:
                        field = self.env[res_model]._fields[res_field]
                    except KeyError:
                        # field does not exist
                        field = None
                    if field is None or not self._has_field_access(field, operation):
                        forbidden_ids.add(att_id)
                        continue
            if res_model and res_id:
                model_ids[res_model].add(res_id)
                att_model_ids.append((att_id, (res_model, res_id)))
        forbidden_res_model_id = set(self._inaccessible_comodel_records(model_ids, operation))
        forbidden_ids.update(att_id for att_id, res in att_model_ids if res in forbidden_res_model_id)

        if forbidden_ids:
            forbidden = self.browse(forbidden_ids)
            forbidden.invalidate_recordset(SECURITY_FIELDS)  # avoid cache pollution
            if error_func is None:
                def error_func():
                    return AccessError(self.env._(
                        "Sorry, you are not allowed to access this document. "
                        "Please contact your system administrator.\n\n"
                        "(Operation: %(operation)s)\n\n"
                        "Records: %(records)s, User: %(user)s",
                        operation=operation,
                        records=forbidden[:6],
                        user=self.env.uid,
                    ))
            return forbidden, error_func
        return None