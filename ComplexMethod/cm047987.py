def write(self, vals):
        """ Update the lead values depending on fields updated in registrations.
        There are 2 main use cases

          * first is when we update the partner_id of multiple registrations. It
            happens when a public user fill its information when they register to
            an event;
          * second is when we update specific values of one registration like
            updating question answers or a contact information (email, phone);

        Also trigger rules based on confirmed and done attendees (state written
        to open and done).
        """
        to_update, event_lead_rule_skip = False, self.env.context.get('event_lead_rule_skip')
        if not event_lead_rule_skip:
            to_update = self.filtered(lambda reg: reg.lead_count)
        if to_update:
            lead_tracked_vals = to_update._get_lead_tracked_values()

        res = super(EventRegistration, self).write(vals)

        if not event_lead_rule_skip and to_update:
            self.env.flush_all()  # compute notably partner-based fields if necessary
            to_update.sudo()._update_leads(vals, lead_tracked_vals)

        # handle triggers based on state
        if not event_lead_rule_skip:
            if vals.get('state') == 'open':
                self.env['event.lead.rule'].search([('lead_creation_trigger', '=', 'confirm')]).sudo()._run_on_registrations(self)
            elif vals.get('state') == 'done':
                self.env['event.lead.rule'].search([('lead_creation_trigger', '=', 'done')]).sudo()._run_on_registrations(self)

        return res