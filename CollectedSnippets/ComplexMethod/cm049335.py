def shop_update_address(self, partner_id, address_type='billing', **kw):
        partner_id = int(partner_id)

        if not (order_sudo := request.cart):
            return

        ResPartner = request.env['res.partner'].sudo()
        partner_sudo = ResPartner.browse(partner_id).exists()
        children = ResPartner._search([
            ('id', 'child_of', order_sudo.partner_id.commercial_partner_id.id),
            ('type', 'in', ('invoice', 'delivery', 'other')),
        ])
        if (
            partner_sudo != order_sudo.partner_id
            and partner_sudo != order_sudo.partner_id.commercial_partner_id
            and partner_sudo.id not in children
        ):
            raise Forbidden()

        partner_fnames = set()
        if (
            address_type == 'billing'
            and partner_sudo != order_sudo.partner_invoice_id
        ):
            partner_fnames.add('partner_invoice_id')
        elif (
            address_type == 'delivery'
            and partner_sudo != order_sudo.partner_shipping_id
        ):
            partner_fnames.add('partner_shipping_id')

        order_sudo._update_address(partner_id, partner_fnames)