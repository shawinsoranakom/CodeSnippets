def _compute_field_value(self, field):
        if field.name != 'invoice_status' or self.env.context.get('mail_activity_automation_skip'):
            return super()._compute_field_value(field)

        # Get SOs which their state is not equal to upselling and if at least a SOL has warning prepaid service upsell set to True and the warning has not already been displayed
        upsellable_orders = self.filtered(lambda so:
            so.state == 'sale'
            and so.invoice_status != 'upselling'
            and so.id
            and (so.user_id or so.partner_id.user_id)  # salesperson needed to assign upsell activity
        )
        super(SaleOrder, upsellable_orders.with_context(mail_activity_automation_skip=True))._compute_field_value(field)
        for order in upsellable_orders:
            upsellable_lines = order._get_prepaid_service_lines_to_upsell()
            if upsellable_lines:
                order._create_upsell_activity()
                # We want to display only one time the warning for each SOL
                upsellable_lines.write({'has_displayed_warning_upsell': True})
        super(SaleOrder, self - upsellable_orders)._compute_field_value(field)