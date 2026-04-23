def _update_leads(self, new_vals, lead_tracked_vals):
        """ Update leads linked to some registrations. Update is based depending
        on updated fields, see ``_get_lead_contact_fields()`` and ``_get_lead_
        description_fields()``. Main heuristic is

          * check attendee-based leads, for each registration recompute contact
            information if necessary (changing partner triggers the whole contact
            computation); update description if necessary;
          * check order-based leads, for each existing group-based lead, only
            partner change triggers a contact and description update. We consider
            that group-based rule works mainly with the main contact and less
            with further details of registrations. Those can be found in stat
            button if necessary.

        :param new_vals: values given to write. Used to determine updated fields;
        :param lead_tracked_vals: dict(registration_id, registration previous values)
          based on new_vals;
        """
        for registration in self:
            leads_attendee = registration.lead_ids.filtered(
                lambda lead: lead.event_lead_rule_id.lead_creation_basis == 'attendee'
            )
            if not leads_attendee:
                continue

            old_vals = lead_tracked_vals[registration.id]
            # if partner has been updated -> update registration contact information
            # as they are computed (and therefore not given to write values)
            if 'partner_id' in new_vals:
                new_vals.update(**dict(
                    (field, registration[field])
                    for field in self._get_lead_contact_fields()
                    if field != 'partner_id')
                )

            lead_values = {}
            # update contact fields: valid for all leads of registration
            upd_contact_fields = [field for field in self._get_lead_contact_fields() if field in new_vals.keys()]
            if any(new_vals[field] != old_vals[field] for field in upd_contact_fields):
                lead_values = registration._get_lead_contact_values()

            # update description fields: each lead has to be updated, otherwise
            # update in batch
            upd_description_fields = [field for field in self._get_lead_description_fields() if field in new_vals.keys()]
            if any(new_vals[field] != old_vals[field] for field in upd_description_fields):
                for lead in leads_attendee:
                    lead_values['description'] = "%s<br/>%s" % (
                        lead.description,
                        registration._get_lead_description(_("Updated registrations"), line_counter=True)
                    )
                    lead.write(lead_values)
            elif lead_values:
                leads_attendee.write(lead_values)

        leads_order = self.lead_ids.filtered(lambda lead: lead.event_lead_rule_id.lead_creation_basis == 'order')
        for lead in leads_order:
            lead_values = {}
            if new_vals.get('partner_id'):
                lead_values.update(lead.registration_ids._get_lead_contact_values())
                if not lead.partner_id:
                    lead_values['description'] = lead.registration_ids._get_lead_description(_("Participants"), line_counter=True)
                elif new_vals['partner_id'] != lead.partner_id.id:
                    lead_values['description'] = (lead.description or '') + "<br/>" + lead.registration_ids._get_lead_description(_("Updated registrations"), line_counter=True, line_suffix=_("(updated)"))
            if lead_values:
                lead.write(lead_values)