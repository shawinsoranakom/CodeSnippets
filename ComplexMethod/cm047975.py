def _process(self, records, domain_post=None):
        """ Process automation ``self`` on the ``records`` that have not been done yet. """
        # filter out the records on which self has already been done
        automation_done = self.env.context.get('__action_done', {})
        records_done = automation_done.get(self, records.browse())
        records -= records_done
        if not records:
            return

        # mark the remaining records as done (to avoid recursive processing)
        if self.env.context.get('__action_feedback'):
            # modify the context dict in place: this is useful when fields are
            # computed during the pre/post filtering, in order to know which
            # automations have already been run by the computation itself
            automation_done[self] = records_done + records
        else:
            automation_done = dict(automation_done)
            automation_done[self] = records_done + records
            self = self.with_context(__action_done=automation_done)
            records = records.with_context(__action_done=automation_done)

        # we process the automation on the records for which any watched field
        # has been modified, and only mark the automation as done for those
        records = records.filtered(self._check_trigger_fields)
        automation_done[self] = records_done + records

        if records and 'date_automation_last' in records._fields:
            records.date_automation_last = self.env.cr.now()

        # prepare the contexts for server actions
        contexts = [
            {
                'active_model': record._name,
                'active_ids': record.ids,
                'active_id': record.id,
                'domain_post': domain_post,
            }
            for record in records
        ]

        # execute server actions
        for action in self.sudo().action_server_ids:
            for ctx in contexts:
                try:
                    action.with_context(**ctx).run()
                except Exception as e:
                    self._add_postmortem(e)
                    raise