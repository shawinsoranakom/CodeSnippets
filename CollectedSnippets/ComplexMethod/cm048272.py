def create(self, vals_list):
        operator_partners_values = [{
            'name': vals['title'],
            'image_1920': vals.get('image_1920', False),
            'active': False,
        } for vals in vals_list if 'operator_partner_id' not in vals and 'title' in vals]

        operator_partners = self.env['res.partner'].create(operator_partners_values)

        for vals, partner in zip(
            [vals for vals in vals_list if 'operator_partner_id' not in vals and 'title' in vals],
            operator_partners
        ):
            vals['operator_partner_id'] = partner.id

        return super().create(vals_list)