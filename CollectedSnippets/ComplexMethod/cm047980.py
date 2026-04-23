def _compute_field_value(self, field):
                # determine fields that may trigger an automation
                stored_fnames = [f.name for f in self.pool.field_computed[field] if f.store]
                if not stored_fnames:
                    return _compute_field_value.origin(self, field)
                # retrieve the action rules to possibly execute
                automations = self.env['base.automation']._get_actions(self, WRITE_TRIGGERS)
                records = self.filtered('id').with_env(automations.env)
                if not (automations and records):
                    _compute_field_value.origin(self, field)
                    return True
                # check preconditions on records
                # changed fields are all fields computed by the function
                changed_fields = [f for f in records._fields.values() if f.compute == field.compute]
                pre = {a: a.with_context(changed_fields=changed_fields)._filter_pre(records) for a in automations}
                # read old values before the update
                old_values = {
                    record.id: {fname: record[fname] for fname in stored_fnames}
                    for record in records
                }
                # call original method
                _compute_field_value.origin(self, field)
                # check postconditions, and execute automations on the records that satisfy them
                for automation in automations.with_context(old_values=old_values):
                    _logger.debug(
                        "Processing automation rule %s (#%s) on %s records (_compute_field_value)",
                        automation.sudo().name, automation.sudo().id, len(records),
                    )
                    records, domain_post = automation._filter_post_export_domain(pre[automation], feedback=True)
                    automation._process(records, domain_post=domain_post)
                return True