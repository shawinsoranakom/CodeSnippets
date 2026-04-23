def res_partner_get(self, email=None, name=None, partner_id=None, **kwargs):
        """
        returns a partner given it's id or an email and a name.
        In case the partner does not exist, we return partner having an id -1, we also look if an existing company
        matching the contact exists in the database, if none is found a new company is enriched and created automatically

        old route name "/mail_client_extension/partner/get is deprecated as of saas-14.3, it is not needed for newer
        versions of the mail plugin but necessary for supporting older versions, only the route name is deprecated not
        the entire method.
        """

        if not (partner_id or (name and email)):
            return {'error': _('You need to specify at least the partner_id or the name and the email')}

        if partner_id:
            partner = request.env['res.partner'].browse(partner_id).exists()
            return self._get_contact_data(partner)

        normalized_email = tools.email_normalize(email)
        if not normalized_email:
            return {'error': _('Bad Email.')}

        notification_emails = request.env['mail.alias.domain'].sudo().search([]).mapped('default_from_email')
        if normalized_email in notification_emails:
            return {
                'partner': {
                    'name': _('Notification'),
                    'email': normalized_email,
                    'enrichment_info': {
                        'type': 'odoo_custom_error', 'info': _('This is your notification address. Search the Contact manually to link this email to a record.'),
                    },
                },
            }

        # Search for the partner based on the email.
        # If multiple are found, take the first one.
        partner = request.env['res.partner'].search(['|', ('email', 'in', [normalized_email, email]),
                                                     ('email_normalized', '=', normalized_email)], limit=1)

        response = self._get_contact_data(partner)

        # if no partner is found in the database, we should also return an empty one having id = -1, otherwise older versions of
        # plugin won't work
        if not response['partner']:
            response['partner'] = {
                'id': -1,
                'email': email,
                'name': name,
                'enrichment_info': None,
            }
            company = self._find_existing_company(normalized_email)

            can_create_partner = request.env['res.partner'].has_access('create')

            if not company and can_create_partner:  # create and enrich company
                company, enrichment_info = self._create_company_from_iap(normalized_email)
                response['partner']['enrichment_info'] = enrichment_info
            response['partner']['company'] = self._get_company_data(company)

        return response