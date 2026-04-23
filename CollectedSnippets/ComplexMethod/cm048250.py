def __try_apply_program(self, program, coupon, status):
        self.ensure_one()
        all_points = status['points']
        points = all_points[0]
        coupons = coupon or self.env['loyalty.card']
        if coupon:
            if program.is_nominative:
                self._add_points_for_coupon({coupon: points})
        elif not coupon:
            # If the program only applies on the current order it does not make sense to fetch already existing coupons
            if program.is_nominative:
                coupon = self.env['loyalty.card'].search(
                    [('partner_id', '=', self.partner_id.id), ('program_id', '=', program.id)], limit=1)
                # Do not apply 'nominative' programs if no point is given and no coupon exists
                if not points and not coupon:
                    return {'error': _("No card found for this loyalty program and no points will be given with this order.")}
                elif coupon:
                    self._add_points_for_coupon({coupon: points})
                coupons = coupon
            if not coupon:
                all_points = [p for p in all_points if p]
                partner = False
                # Loyalty programs and ewallets are nominative
                if program.is_nominative or program.program_type == 'next_order_coupons':
                    partner = self.partner_id.id
                coupons = self.env['loyalty.card'].sudo().with_context(loyalty_no_mail=True, tracking_disable=True).create([{
                    'program_id': program.id,
                    'partner_id': partner,
                    'points': 0,
                    'order_id': self.id,
                } for _ in all_points])
                self._add_points_for_coupon({coupon: x for coupon, x in zip(coupons, all_points)})
        return {'coupon': coupons}