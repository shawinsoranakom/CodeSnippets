def action_validate(self):
        records_done = self.env['data_recycle.record']
        record_ids_to_archive = defaultdict(list)
        record_ids_to_unlink = defaultdict(list)
        original_records = {'%s_%s' % (r._name, r.id): r for r in self._original_records()}
        for record in self:
            original_record = original_records.get('%s_%s' % (record.res_model_name, record.res_id))
            records_done |= record
            if not original_record:
                continue
            if record.recycle_model_id.recycle_action == "archive":
                record_ids_to_archive[original_record._name].append(original_record.id)
            elif record.recycle_model_id.recycle_action == "unlink":
                record_ids_to_unlink[original_record._name].append(original_record.id)
        for model_name, ids in record_ids_to_archive.items():
            self.env[model_name].sudo().browse(ids).action_archive()
        for model_name, ids in record_ids_to_unlink.items():
            self.env[model_name].sudo().browse(ids).unlink()
        records_done.unlink()