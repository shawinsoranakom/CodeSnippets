def res_partner_enrich_and_update_company(self, partner_id):
        """
        Enriches an existing company using IAP
        """
        partner = request.env['res.partner'].browse(partner_id).exists()

        if not partner:
            return {'error': _("This partner does not exist")}

        if not partner.is_company:
            return {'error': 'Contact must be a company'}

        normalized_email = partner.email_normalized
        if not normalized_email:
            return {'error': 'The email of this contact is not valid and we can not enrich it'}

        domain = tools.email_domain_extract(normalized_email)
        iap_data = self._iap_enrich(domain)

        if 'enrichment_info' in iap_data:  # means that an issue happened with the enrichment request
            return {
                'enrichment_info': iap_data['enrichment_info'],
                'company': self._get_company_data(partner),
            }

        phone_numbers = iap_data.get('phone_numbers')

        partner_values = {}

        if not partner.phone and phone_numbers:
            partner_values.update({'phone': phone_numbers[0]})

        if not partner.iap_enrich_info:
            partner_values.update({'iap_enrich_info': json.dumps(iap_data)})

        if not partner.image_128:
            logo_url = iap_data.get('logo')
            if logo_url:
                try:
                    response = requests.get(logo_url, timeout=2)
                    if response.ok:
                        partner_values.update({'image_1920': base64.b64encode(response.content)})
                except Exception:
                    pass

        model_fields_to_iap_mapping = {
            'street': 'street_name',
            'city': 'city',
            'zip': 'postal_code',
            'website': 'domain',
        }

        # only update keys for which we dont have values yet
        partner_values.update({
            model_field: iap_data.get(iap_key)
            for model_field, iap_key in model_fields_to_iap_mapping.items() if not partner[model_field]
        })

        partner.write(partner_values)

        partner.message_post_with_source(
            'iap_mail.enrich_company',
            render_values=iap_data,
            subtype_xmlid='mail.mt_note',
        )

        return {
            'enrichment_info': {'type': 'company_updated'},
            'company': self._get_company_data(partner),
        }