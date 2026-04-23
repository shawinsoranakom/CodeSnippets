def _recycle_records(self, batch_commits=False):
        self.env.flush_all()
        records_to_clean = []
        is_test = modules.module.current_test

        existing_recycle_records = self.env['data_recycle.record'].with_context(
            active_test=False).search([('recycle_model_id', 'in', self.ids)])
        mapped_existing_records = defaultdict(list)
        for recycle_record in existing_recycle_records:
            mapped_existing_records[recycle_record.recycle_model_id].append(recycle_record.res_id)

        for recycle_model in self:
            rule_domain = Domain(ast.literal_eval(recycle_model.domain)) if recycle_model.domain and recycle_model.domain != '[]' else Domain.TRUE
            if recycle_model.time_field_id and recycle_model.time_field_delta and recycle_model.time_field_delta_unit:
                if recycle_model.time_field_id.ttype == 'date':
                    now = fields.Date.today()
                else:
                    now = fields.Datetime.now()
                delta = relativedelta(**{recycle_model.time_field_delta_unit: recycle_model.time_field_delta})
                rule_domain &= Domain(recycle_model.time_field_id.name, '<=', now - delta)
            model = self.env[recycle_model.res_model_name]
            if recycle_model.include_archived:
                model = model.with_context(active_test=False)
            records_to_recycle = model.search(rule_domain)
            records_to_create = [{
                'res_id': record.id,
                'recycle_model_id': recycle_model.id,
            } for record in records_to_recycle if record.id not in mapped_existing_records[recycle_model]]

            if recycle_model.recycle_mode == 'automatic':
                for records_to_create_batch in split_every(DR_CREATE_STEP_AUTO, records_to_create):
                    self.env['data_recycle.record'].create(records_to_create_batch).action_validate()
                    if batch_commits and not is_test:
                        # Commit after each batch iteration to avoid complete rollback on timeout as
                        # this can create lots of new records.
                        self.env.cr.commit()
            else:
                records_to_clean = records_to_clean + records_to_create
        for records_to_clean_batch in split_every(DR_CREATE_STEP_MANUAL, records_to_clean):
            self.env['data_recycle.record'].create(records_to_clean_batch)
            if batch_commits and not is_test:
                self.env.cr.commit()