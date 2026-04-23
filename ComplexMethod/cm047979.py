def write(self, vals, **kw):
                # retrieve the automation rules to possibly execute
                automations = self.env['base.automation']._get_actions(self, WRITE_TRIGGERS)
                if not (automations and self):
                    return write.origin(self, vals, **kw)
                records = self.with_env(automations.env).filtered('id')
                # check preconditions on records
                pre = {a: a._filter_pre(records) for a in automations}
                # read old values before the update
                old_values = {
                    record.id: {field_name: record[field_name] for field_name in vals if field_name in record._fields and record._fields[field_name].store}
                    for record in records
                }
                # call original method
                write.origin(self.with_env(automations.env), vals, **kw)
                # check postconditions, and execute actions on the records that satisfy them
                for automation in automations.with_context(old_values=old_values):
                    _logger.debug(
                        "Processing automation rule %s (#%s) on %s records (write)",
                        automation.sudo().name, automation.sudo().id, len(records),
                    )
                    records, domain_post = automation._filter_post_export_domain(pre[automation], feedback=True)
                    automation._process(records, domain_post=domain_post)
                return True