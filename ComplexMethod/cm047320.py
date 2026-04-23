def delete(records):
            # do not delete records that have other external ids (and thus do
            # not belong to the modules being installed)
            ref_data = self.search([
                ('model', '=', records._name),
                ('res_id', 'in', records.ids),
            ])
            cloc_exclude_data = ref_data.filtered(lambda imd: imd.module == '__cloc_exclude__')
            ref_data -= cloc_exclude_data
            records -= records.browse((ref_data - module_data).mapped('res_id'))
            if not records:
                return

            # special case for ir.model.fields
            if records._name == 'ir.model.fields':
                missing = records - records.exists()
                if missing:
                    # delete orphan external ids right now;
                    # an orphan ir.model.data can happen if the ir.model.field is deleted via
                    # an ONDELETE CASCADE, in which case we must verify that the records we're
                    # processing exist in the database otherwise a MissingError will be raised
                    orphans = ref_data.filtered(lambda r: r.res_id in missing._ids)
                    _logger.info('Deleting orphan ir_model_data %s', orphans)
                    orphans.unlink()
                    # /!\ this must go before any field accesses on `records`
                    records -= missing
                # do not remove LOG_ACCESS_COLUMNS unless _log_access is False
                # on the model
                records -= records.filtered(lambda f: f.name == 'id' or (
                    f.name in models.LOG_ACCESS_COLUMNS and
                    f.model in self.env and self.env[f.model]._log_access
                ))

            # now delete the records
            _logger.info('Deleting %s', records)
            try:
                with self.env.cr.savepoint():
                    cloc_exclude_data.unlink()
                    records.unlink()
            except Exception:
                if len(records) <= 1:
                    undeletable_ids.extend(ref_data._ids)
                else:
                    # divide the batch in two, and recursively delete them
                    half_size = len(records) // 2
                    delete(records[:half_size])
                    delete(records[half_size:])