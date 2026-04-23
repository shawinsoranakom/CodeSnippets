def action_mass_convert(self):
        self.ensure_one()
        if self.name == 'convert' and self.deduplicate:
            # TDE CLEANME: still using active_ids from context
            active_ids = self.env.context.get('active_ids', [])
            merged_lead_ids = set()
            remaining_lead_ids = set()
            for lead in self.lead_tomerge_ids:
                if lead.id not in merged_lead_ids:
                    duplicated_leads = self.env['crm.lead']._get_lead_duplicates(
                        partner=lead.partner_id,
                        email=lead.partner_id.email or lead.email_from,
                        include_lost=False
                    )
                    if len(duplicated_leads) > 1:
                        lead = duplicated_leads.merge_opportunity()
                        merged_lead_ids.update(duplicated_leads.ids)
                        remaining_lead_ids.add(lead.id)
            # rebuild list of lead IDS to convert, following given order
            final_ids = [lead_id for lead_id in active_ids if lead_id not in merged_lead_ids]
            final_ids += [lead_id for lead_id in remaining_lead_ids if lead_id not in final_ids]

            self = self.with_context(active_ids=final_ids)  # only update active_ids when there are set
        return self.action_apply()