def _update_reference_fields_generic(self, referenced_model, src_records, dst_record, additional_update_records=None):
        """ Update all reference fields from the src_records to dst_record for any model.
            :param referenced_model: model name as a string
            :param src_records: merge source recordset (does not include destination one)
            :param dst_record: record of destination
            :param additional_update_records: list of tuples (model, field_model, field_id)
        """
        _logger.debug('_update_reference_fields_generic for dst_record: %s for src_records: %r', dst_record.id, src_records.ids)

        def update_records(model, src, field_model='model', field_id='res_id'):
            Model = self.env[model] if model in self.env else None
            if Model is None:
                return
            records = Model.sudo().search([(field_model, '=', referenced_model), (field_id, '=', src.id)])
            if not records:
                return
            if not self._has_check_or_unique_constraint(records._table, field_id):
                records.sudo().write({field_id: dst_record.id})
                records.env.flush_all()
                return
            try:
                with mute_logger('odoo.sql_db'), self.env.cr.savepoint():
                    records.sudo().write({field_id: dst_record.id})
                    records.env.flush_all()
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent partner_id is useless, better delete it
                records.sudo().unlink()

        for record in src_records:
            update_records('ir.attachment', src=record, field_model='res_model')
            update_records('mail.followers', src=record, field_model='res_model')
            update_records('mail.activity', src=record, field_model='res_model')
            update_records('mail.message', src=record)
            update_records('ir.model.data', src=record)

        additional_update_records = additional_update_records or []
        for update_record in additional_update_records:
            update_records(update_record['model'], src=record, field_model=update_record['field_model'])

        records = self.env['ir.model.fields'].sudo().search([('ttype', '=', 'reference'), ('store', '=', True)])
        for record in records:
            try:
                Model = self.env[record.model]
                field = Model._fields[record.name]
            except KeyError:
                # unknown model or field => skip
                continue

            if Model._abstract or field.compute is not None:
                continue

            for src_record in src_records:
                records_ref = Model.sudo().search([(record.name, '=', '%s,%d' % (referenced_model, src_record.id))])
                values = {
                    record.name: '%s,%d' % (referenced_model, dst_record.id),
                }
                records_ref.sudo().write(values)
        # company_dependent fields referring the merged records
        for field in self.env.registry.many2one_company_dependents[dst_record._name]:
            self.env.cr.execute(SQL(
                """
                UPDATE %(table)s
                SET %(field)s = (
                    SELECT jsonb_object_agg(key,
                        CASE
                            WHEN value::int IN %(src_record_ids)s
                            THEN %(dest_record_id)s
                            ELSE value::int
                        END
                    )
                    FROM jsonb_each_text(%(field)s)
                )
                WHERE %(field)s IS NOT NULL
                """,
                table=SQL.identifier(self.env[field.model_name]._table),
                field=SQL.identifier(field.name),
                src_record_ids=tuple(src_records.ids),
                dest_record_id=dst_record.id,
            ))

        # merge the fallback values for company dependent many2one fields
        self.env.cr.execute(SQL(
            """
            UPDATE ir_default
            SET json_value =
                CASE
                    WHEN json_value::int IN %(src_record_ids)s
                    THEN %(dest_record_id)s
                    ELSE json_value
                END
            FROM ir_model_fields f
            WHERE f.id = ir_default.field_id
            AND f.company_dependent
            AND f.relation = %(model_name)s
            AND f.ttype = 'many2one'
            AND json_value ~ '^[0-9]+$';
            """,
            src_record_ids=tuple(src_records.ids),
            dest_record_id=str(dst_record.id),
            model_name=dst_record._name,
        ))

        self.env.flush_all()

        # company_dependent fields of merged records
        for fname, field in dst_record._fields.items():
            if not field.company_dependent:
                continue
            self.env.execute_query(SQL(
                # use the specific company dependent value of sources
                # to fill the non-specific value of destination. Source
                # values for rows with larger id have higher priority
                # when aggregated
                """
                WITH source AS (
                    SELECT %(field)s
                    FROM  %(table)s
                    WHERE id IN %(source_ids)s
                    ORDER BY id
                ), source_agg AS (
                    SELECT jsonb_object_agg(key, value) AS value
                    FROM  source, jsonb_each(%(field)s)
                )
                UPDATE %(table)s
                SET %(field)s = source_agg.value || COALESCE(%(table)s.%(field)s, '{}'::jsonb)
                FROM source_agg
                WHERE id = %(destination_id)s AND source_agg.value IS NOT NULL
                """,
                table=SQL.identifier(dst_record._table),
                field=SQL.identifier(fname),
                destination_id=dst_record.id,
                source_ids=tuple(src_records.ids),
            ))