def _create_customer(self, with_parent=None):
        """ Create a partner from lead data and link it to the lead.

        :param with_parent: if set, create the new partner with the given parent
        :return: newly-created partner browse record
        """
        Partner = self.env['res.partner']
        contact_name = self.contact_name
        if not contact_name:
            contact_name = parse_contact_from_email(self.email_from)[0] if self.email_from else False

        if with_parent:
            partner_company = with_parent
        elif self.partner_name:
            partner_company = Partner.create(self._prepare_customer_values(self.partner_name, is_company=True))
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            partner_company = self.env['res.partner']

        if contact_name:
            return Partner.create(self._prepare_customer_values(contact_name, is_company=False, parent_id=partner_company.id))

        if partner_company:
            return partner_company
        return Partner.create(self._prepare_customer_values(self.name, is_company=False))