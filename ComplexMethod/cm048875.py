def write(self, vals):
        link_tracker_vals = {}
        if vals.keys() & set(self._get_render_fields()):
            self.env['card.card'].with_context(active_test=False).search([('campaign_id', 'in', self.ids)]).requires_sync = True
        if 'target_url' in vals:
            link_tracker_vals['url'] = vals['target_url'] or self.env['card.campaign'].get_base_url()
        if link_tracker_vals:
            self.link_tracker_id.sudo().write(link_tracker_vals)

        # write and detect model changes on actively-used campaigns
        original_models = self.mapped('res_model')

        write_res = super().write(vals)

        updated_model_campaigns = self.env['card.campaign'].browse([
            campaign.id for campaign, new_model, old_model
            in zip(self, self.mapped('res_model'), original_models)
            if new_model != old_model
        ])
        for campaign in updated_model_campaigns:
            if campaign.card_count:
                raise exceptions.ValidationError(_(
                    "Model of campaign %(campaign)s may not be changed as it already has cards",
                    campaign=campaign.display_name,
                ))
        return write_res