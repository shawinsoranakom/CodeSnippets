def partner_desinterested(self, comment=False, contacted=False, spam=False):
        self._assert_portal_write_access()
        if contacted:
            message = Markup('<p>%s</p>') % _('I am not interested by this lead. I contacted the lead.')
        else:
            message = Markup('<p>%s</p>') % _('I am not interested by this lead. I have not contacted the lead.')
        partner_ids = self.env['res.partner'].search(
            [('id', 'child_of', self.env.user.partner_id.commercial_partner_id.id)])
        self.sudo().message_unsubscribe(partner_ids=partner_ids.ids)
        if comment:
            message += Markup('<p>%s</p>') % comment
        self.sudo().message_post(body=message)
        values = {
            'partner_assigned_id': False,
        }

        if spam:
            tag_spam = self.env.ref('website_crm_partner_assign.tag_portal_lead_is_spam', False)
            if tag_spam and tag_spam not in self.sudo().tag_ids:
                values['tag_ids'] = [(4, tag_spam.id, False)]
        if partner_ids:
            values['partner_declined_ids'] = [(4, p, 0) for p in partner_ids.ids]
        self.sudo().write(values)