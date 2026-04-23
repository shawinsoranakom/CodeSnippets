def _compute_registration_status(self):
        for sale_order, registrations in self.filtered('sale_order_id').grouped('sale_order_id').items():
            cancelled_so_registrations = registrations.filtered(lambda reg: reg.sale_order_id.state == 'cancel')
            cancelled_so_registrations.state = 'cancel'
            cancelled_registrations = cancelled_so_registrations | registrations.filtered(lambda reg: reg.state == 'cancel')
            if float_is_zero(sale_order.amount_total, precision_rounding=sale_order.currency_id.rounding):
                registrations.sale_status = 'free'
                registrations.filtered(lambda reg: not reg.state or reg.state == 'draft').state = "open"
            else:
                sold_registrations = registrations.filtered(lambda reg: reg.sale_order_id.state == 'sale') - cancelled_registrations
                sold_registrations.sale_status = 'sold'
                (registrations - sold_registrations).sale_status = 'to_pay'
                sold_registrations.filtered(lambda reg: not reg.state or reg.state in {'draft', 'cancel'}).state = "open"
                (registrations - sold_registrations - cancelled_registrations).state = 'draft'
        super()._compute_registration_status()

        # set default value to free and open if none was set yet
        for registration in self:
            if not registration.sale_status:
                registration.sale_status = 'free'
            if not registration.state:
                registration.state = 'open'