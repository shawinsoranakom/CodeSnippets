def _stripe_create_customer(self):
        """ Create and return a Customer.

        :return: The Customer
        :rtype: dict
        """
        customer = self._send_api_request(
            'POST', 'customers', data={
                'address[city]': self.partner_city or None,
                'address[country]': self.partner_country_id.code or None,
                'address[line1]': self.partner_address or None,
                'address[postal_code]': self.partner_zip or None,
                'address[state]': self.partner_state_id.name or None,
                'description': f'Odoo Partner: {self.partner_id.name} (id: {self.partner_id.id})',
                'email': self.partner_email or None,
                'name': self.partner_name,
                'phone': self.partner_phone and self.partner_phone[:20] or None,
            }
        )
        return customer