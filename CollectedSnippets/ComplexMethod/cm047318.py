def _module_data_uninstall(self, modules_to_remove):
        """Deletes all the records referenced by the ir.model.data entries
        ``ids`` along with their corresponding database backed (including
        dropping tables, columns, FKs, etc, as long as there is no other
        ir.model.data entry holding a reference to them (which indicates that
        they are still owned by another module).
        Attempts to perform the deletion in an appropriate order to maximize
        the chance of gracefully deleting all records.
        This step is performed as part of the full uninstallation of a module.
        """
        from odoo.orm.model_classes import add_field

        if not self.env.is_system():
            raise AccessError(_('Administrator access is required to uninstall a module'))

        # enable model/field deletion
        # we deactivate prefetching to not try to read a column that has been deleted
        self = self.with_context(**{MODULE_UNINSTALL_FLAG: True, 'prefetch_fields': False})

        # determine records to unlink
        records_items = []              # [(model, id)]
        model_ids = []
        field_ids = []
        selection_ids = []
        constraint_ids = []

        module_data = self.search([('module', 'in', modules_to_remove)], order='id DESC')
        for data in module_data:
            if data.model == 'ir.model':
                model_ids.append(data.res_id)
            elif data.model == 'ir.model.fields':
                field_ids.append(data.res_id)
            elif data.model == 'ir.model.fields.selection':
                selection_ids.append(data.res_id)
            elif data.model == 'ir.model.constraint':
                constraint_ids.append(data.res_id)
            else:
                records_items.append((data.model, data.res_id))

        # avoid prefetching fields that are going to be deleted: during uninstall, it is
        # possible to perform a recompute (via flush) after the database columns have been
        # deleted but before the new registry has been created, meaning the recompute will
        # be executed on a stale registry, and if some of the data for executing the compute
        # methods is not in cache it will be fetched, and fields that exist in the registry but not
        # in the database will be prefetched, this will of course fail and prevent the uninstall.
        has_shared_field = False
        for ir_field in self.env['ir.model.fields'].browse(field_ids):
            model = self.pool.get(ir_field.model)
            if model is not None:
                field = model._fields.get(ir_field.name)
                if field is not None and field.prefetch:
                    if field._toplevel:
                        # the field is specific to this registry
                        field.prefetch = False
                    else:
                        # the field is shared across registries; don't modify it
                        Field = type(field)
                        field_ = Field(_base_fields__=(field, Field(prefetch=False)))
                        add_field(self.env.registry[ir_field.model], ir_field.name, field_)
                        field_.setup(model)
                        has_shared_field = True
        if has_shared_field:
            registry = self.env.registry
            reset_cached_properties(registry)
            registry._field_trigger_trees.clear()
            registry._is_modifying_relations.clear()

        # to collect external ids of records that cannot be deleted
        undeletable_ids = []

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

        # remove non-model records first, grouped by batches of the same model
        for model, items in itertools.groupby(unique(records_items), itemgetter(0)):
            ids = [item[1] for item in items]
            # we cannot guarantee that the ir.model.data points to an existing model
            if model in self.env:
                delete(self.env[model].browse(ids))
            else:
                _logger.info("Orphan ir.model.data records %s refer to unavailable model '%s'", ids, model)

        # Remove copied views. This must happen after removing all records from
        # the modules to remove, otherwise ondelete='restrict' may prevent the
        # deletion of some view. This must also happen before cleaning up the
        # database schema, otherwise some dependent fields may no longer exist
        # in database.
        modules = self.env['ir.module.module'].search([('name', 'in', modules_to_remove)])
        modules._remove_copied_views()

        # remove constraints
        delete(self.env['ir.model.constraint'].browse(unique(constraint_ids)))

        # If we delete a selection field, and some of its values have ondelete='cascade',
        # we expect the records with that value to be deleted. If we delete the field first,
        # the column is dropped and the selection is gone, and thus the records above will not
        # be deleted.
        delete(self.env['ir.model.fields.selection'].browse(unique(selection_ids)).exists())
        delete(self.env['ir.model.fields'].browse(unique(field_ids)))
        relations = self.env['ir.model.relation'].search([('module', 'in', modules.ids)])
        relations._module_data_uninstall()

        # remove models
        delete(self.env['ir.model'].browse(unique(model_ids)))

        # log undeletable ids
        _logger.info("ir.model.data could not be deleted (%s)", undeletable_ids)

        # sort out which undeletable model data may have become deletable again because
        # of records being cascade-deleted or tables being dropped just above
        for data in self.browse(undeletable_ids).exists():
            record = self.env[data.model].browse(data.res_id)
            try:
                with self.env.cr.savepoint():
                    if record.exists():
                        # record exists therefore the data is still undeletable,
                        # remove it from module_data
                        module_data -= data
                        continue
            except psycopg2.ProgrammingError:
                # This most likely means that the record does not exist, since record.exists()
                # is rougly equivalent to `SELECT id FROM table WHERE id=record.id` and it may raise
                # a ProgrammingError because the table no longer exists (and so does the
                # record), also applies to ir.model.fields, constraints, etc.
                pass
        # remove remaining module data records
        module_data.unlink()