def generate_coupons(self):
        if any(not wizard.program_id for wizard in self):
            raise ValidationError(_("Can not generate coupon, no program is set."))
        if any(wizard.coupon_qty <= 0 for wizard in self):
            raise ValidationError(_("Invalid quantity."))
        coupon_create_vals = []
        for wizard in self:
            customers = wizard._get_partners() or range(wizard.coupon_qty)
            for partner in customers:
                coupon_create_vals.append(wizard._get_coupon_values(partner))
        coupons = self.env['loyalty.card'].create(coupon_create_vals)
        self.env['loyalty.history'].create([
            {
                'description': self.description or _("Gift For Customer"),
                'card_id': coupon.id,
                'issued': self.points_granted,
            } for coupon in coupons
        ])
        return coupons