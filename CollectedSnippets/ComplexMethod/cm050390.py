def _get_fiscal_state(order):
            """
            Maps each order to its corresponding fiscal state based on its type,
            fiscal conditions, and the state of the associated partner or company.
            """

            partner_to_consider = order.partner_invoice_id or order.partner_id
            if partner_to_consider.l10n_in_gst_treatment == 'special_economic_zone':
                # Special Economic Zone
                return sez_state

            # Computing Place of Supply for particular order
            partner = (
                partner_to_consider.commercial_partner_id == order.partner_shipping_id.commercial_partner_id
                and order.partner_shipping_id
                or partner_to_consider
            )
            if partner.country_id and partner.country_id.code != 'IN':
                return foreign_state
            partner_state = partner.state_id or partner_to_consider.commercial_partner_id.state_id or order.company_id.state_id
            country_code = partner_state.country_id.code or order.country_code
            return partner_state if country_code == 'IN' else foreign_state