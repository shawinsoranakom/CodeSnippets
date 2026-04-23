def _compute_im_status(self):
        for partner in self:
            all_status = partner.user_ids.presence_ids.mapped(
                lambda p: "offline" if p.status == "offline" else p.user_id.manual_im_status or p.status
            )
            partner.im_status = (
                "online"
                if "online" in all_status
                else "away"
                if "away" in all_status
                else "busy"
                if "busy" in all_status
                else "offline"
                if partner.user_ids
                else "im_partner"
            )
            partner.offline_since = (
                max(partner.user_ids.presence_ids.mapped("last_poll"), default=None)
                if partner.im_status == "offline"
                else None
            )
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id('base.partner_root')
        odoobot = self.env['res.partner'].browse(odoobot_id)
        if odoobot in self:
            odoobot.im_status = 'bot'