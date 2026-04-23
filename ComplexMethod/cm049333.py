def _prepare_address_update(self, order_sudo, partner_id=None, address_type=None):
        """ Find the partner whose address to update and return it along with its address type.

        :param sale.order order_sudo: The current cart.
        :param int partner_id: The partner whose address to update, if any, as a `res.partner` id.
        :param str address_type: The type of the address: 'billing' or 'delivery'.
        :return: The partner whose address to update, if any, and its address type.
        :rtype: tuple[res.partner, str]
        :raise Forbidden: If the customer is not allowed to update the given address.
        """
        PartnerSudo = request.env['res.partner'].with_context(show_address=1).sudo()
        if order_sudo._is_anonymous_cart():
            partner_sudo = PartnerSudo
        else:
            partner_sudo = PartnerSudo.browse(partner_id)
            if partner_sudo and partner_sudo not in {
                order_sudo.partner_id,
                order_sudo.partner_invoice_id,
                order_sudo.partner_shipping_id,
            }:  # The partner is not yet linked to the SO.
                partner_sudo = partner_sudo.exists()

        if partner_sudo and not address_type:  # The desired address type was not specified.
            # Identify the address type based on the cart's billing and delivery partners.
            if partner_id == order_sudo.partner_invoice_id.id:
                address_type = 'billing'
            elif partner_id == order_sudo.partner_shipping_id.id:
                address_type = 'delivery'
            else:
                address_type = 'billing'

        if (
            partner_sudo
            and not partner_sudo._can_be_edited_by_current_customer(order_sudo=order_sudo)
        ):
            raise Forbidden()

        return partner_sudo, address_type