def _process_end(self, modules):
        """ Clear records removed from updated module data.
        This method is called at the end of the module loading process.
        It is meant to removed records that are no longer present in the
        updated data. Such records are recognised as the one with an xml id
        and a module in ir_model_data and noupdate set to false, but not
        present in self.pool.loaded_xmlids.
        """
        if not modules or tools.config.get('import_partial'):
            return True

        bad_imd_ids = []
        self = self.with_context({MODULE_UNINSTALL_FLAG: True})
        loaded_xmlids = self.pool.loaded_xmlids

        query = """ SELECT id, module || '.' || name, model, res_id FROM ir_model_data
                    WHERE module IN %s AND res_id IS NOT NULL AND COALESCE(noupdate, false) != %s ORDER BY id DESC
                """
        self.env.cr.execute(query, (tuple(modules), True))
        for (id, xmlid, model, res_id) in self.env.cr.fetchall():
            if xmlid in loaded_xmlids:
                continue

            Model = self.env.get(model)
            if Model is None:
                continue

            # when _inherits parents are implicitly created we give them an
            # external id (if their descendant has one) in order to e.g.
            # properly remove them when the module is deleted, however this
            # generated id is *not* provided during update yet we don't want to
            # try and remove either the xid or the record, so check if the
            # record has a child we've just updated
            keep = False
            for inheriting in (self.env[m] for m in Model._inherits_children):
                # ignore mixins
                if inheriting._abstract:
                    continue

                parent_field = inheriting._inherits[model]
                children = inheriting.with_context(active_test=False).search([(parent_field, '=', res_id)])
                children_xids = {
                    xid
                    for xids in (children and children._get_external_ids().values())
                    for xid in xids
                }
                if children_xids & loaded_xmlids:
                    # at least one child was loaded
                    keep = True
                    break
            if keep:
                continue

            # if the record has other associated xids, only remove the xid
            if self.search_count([
                ("model", "=", model),
                ("res_id", "=", res_id),
                ("id", "!=", id),
                ("id", "not in", bad_imd_ids),
            ]):
                bad_imd_ids.append(id)
                continue

            _logger.info('Deleting %s@%s (%s)', res_id, model, xmlid)
            record = Model.browse(res_id)
            if record.exists():
                module = xmlid.split('.', 1)[0]
                record = record.with_context(module=module)
                self._process_end_unlink_record(record)
            else:
                bad_imd_ids.append(id)
        if bad_imd_ids:
            self.browse(bad_imd_ids).unlink()

        # Once all views are created create specific ones
        self.env['ir.ui.view']._create_all_specific_views(modules)

        loaded_xmlids.clear()