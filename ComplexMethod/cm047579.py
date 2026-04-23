def unlink(self) -> typing.Literal[True]:
        """ Delete the records in ``self``.

        :raise AccessError: if the user is not allowed to delete all the given records
        :raise UserError: if the record is default property for other records
        """
        if not self:
            return True

        self.check_access('unlink')

        from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
        for func in self._ondelete_methods:
            # func._ondelete is True if it should be called during uninstallation
            if func._ondelete or not self.env.context.get(MODULE_UNINSTALL_FLAG):
                func(self)

        # TOFIX: this avoids an infinite loop when trying to recompute a
        # field, which triggers the recomputation of another field using the
        # same compute function, which then triggers again the computation
        # of those two fields
        for field in self._fields.values():
            self.env.remove_to_compute(field, self)

        self.env.flush_all()

        cr = self.env.cr
        Data = self.env['ir.model.data'].sudo().with_context({})
        Defaults = self.env['ir.default'].sudo()
        Attachment = self.env['ir.attachment'].sudo()
        ir_model_data_unlink = Data
        ir_attachment_unlink = Attachment

        # mark fields that depend on 'self' to recompute them after 'self' has
        # been deleted (like updating a sum of lines after deleting one line)
        with self.env.protecting(self._fields.values(), self):
            self.modified(self._fields, before=True)

        for sub_ids in split_every(cr.IN_MAX, self.ids):
            records = self.browse(sub_ids)

            cr.execute(SQL(
                "DELETE FROM %s WHERE id IN %s",
                SQL.identifier(self._table), sub_ids,
            ))

            # Removing the ir_model_data reference if the record being deleted
            # is a record created by xml/csv file, as these are not connected
            # with real database foreign keys, and would be dangling references.
            #
            # Note: the following steps are performed as superuser to avoid
            # access rights restrictions, and with no context to avoid possible
            # side-effects during admin calls.
            data = Data.search([('model', '=', self._name), ('res_id', 'in', sub_ids)])
            ir_model_data_unlink |= data

            # For the same reason, remove the relevant records in ir_attachment
            # (the search is performed with sql as the search method of
            # ir_attachment is overridden to hide attachments of deleted
            # records)
            cr.execute(SQL(
                "SELECT id FROM ir_attachment WHERE res_model=%s AND res_id IN %s",
                self._name, sub_ids,
            ))
            ir_attachment_unlink |= Attachment.browse(row[0] for row in cr.fetchall())

            # don't allow fallback value in ir.default for many2one company dependent fields to be deleted
            # Exception: when MODULE_UNINSTALL_FLAG, these fallbacks can be deleted by Defaults.discard_records(records)
            if (many2one_fields := self.env.registry.many2one_company_dependents[self._name]) and not self.env.context.get(MODULE_UNINSTALL_FLAG):
                IrModelFields = self.env["ir.model.fields"]
                field_ids = tuple(IrModelFields._get_ids(field.model_name).get(field.name) for field in many2one_fields)
                sub_ids_json_text = tuple(json.dumps(id_) for id_ in sub_ids)
                if default := Defaults.search([('field_id', 'in', field_ids), ('json_value', 'in', sub_ids_json_text)], limit=1, order='id desc'):
                    ir_field = default.field_id.sudo()
                    field = self.env[ir_field.model]._fields[ir_field.name]
                    record = self.browse(json.loads(default.json_value))
                    raise UserError(_('Unable to delete %(record)s because it is used as the default value of %(field)s', record=record, field=field))

            # on delete set null/restrict for jsonb company dependent many2one
            for field in many2one_fields:
                model = self.env[field.model_name]
                if field.ondelete == 'restrict' and not self.env.context.get(MODULE_UNINSTALL_FLAG):
                    if res := self.env.execute_query(SQL(
                        """
                        SELECT id, %(field)s
                        FROM %(table)s
                        WHERE %(field)s IS NOT NULL
                        AND %(field)s @? %(jsonpath)s
                        ORDER BY id
                        LIMIT 1
                        """,
                        table=SQL.identifier(model._table),
                        field=SQL.identifier(field.name),
                        jsonpath=f"$.* ? ({' || '.join(f'@ == {id_}' for id_ in sub_ids)})",
                    )):
                        on_restrict_id, field_json = res[0]
                        to_delete_id = next(iter(id_ for id_ in field_json.values()))
                        on_restrict_record = model.browse(on_restrict_id)
                        to_delete_record = self.browse(to_delete_id)
                        raise UserError(_('You cannot delete %(to_delete_record)s, as it is used by %(on_restrict_record)s',
                                          to_delete_record=to_delete_record, on_restrict_record=on_restrict_record))
                else:
                    self.env.execute_query(SQL(
                        """
                        UPDATE %(table)s
                        SET %(field)s = (
                            SELECT jsonb_object_agg(
                                key,
                                CASE
                                    WHEN value::int4 in %(ids)s THEN NULL
                                    ELSE value::int4
                                END)
                            FROM jsonb_each_text(%(field)s)
                        )
                        WHERE %(field)s IS NOT NULL
                        AND %(field)s @? %(jsonpath)s
                        """,
                        table=SQL.identifier(model._table),
                        field=SQL.identifier(field.name),
                        ids=sub_ids,
                        jsonpath=f"$.* ? ({' || '.join(f'@ == {id_}' for id_ in sub_ids)})",
                    ))

            # For the same reason, remove the defaults having some of the
            # records as value
            Defaults.discard_records(records)

        # invalidate the *whole* cache, since the orm does not handle all
        # changes made in the database, like cascading delete!
        self.env.invalidate_all(flush=False)
        if ir_model_data_unlink:
            ir_model_data_unlink.unlink()
        if ir_attachment_unlink:
            ir_attachment_unlink.unlink()

        # auditing: deletions are infrequent and leave no trace in the database
        _unlink.info('User #%s deleted %s records with IDs: %r', self.env.uid, self._name, self.ids)

        return True