def _compute_show_enrich_button(self):
        for lead in self:
            if not lead.active or not lead.email_from or lead.email_state == 'incorrect' or lead.iap_enrich_done or lead.reveal_id or lead.probability == 100:
                lead.show_enrich_button = False
            else:
                lead.show_enrich_button = True