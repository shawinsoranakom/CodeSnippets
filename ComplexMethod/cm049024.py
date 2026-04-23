def _create_invoices(self, sale_orders):
        self.ensure_one()
        if self.advance_payment_method == 'delivered':
            return sale_orders._create_invoices(final=self.deduct_down_payments, grouped=not self.consolidated_billing)
        else:
            self.sale_order_ids.ensure_one()
            self = self.with_company(self.company_id)
            order = self.sale_order_ids

            AccountTax = self.env['account.tax']
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)

            if self.advance_payment_method == 'percentage':
                amount_type = 'percent'
                amount = self.amount
            else:  # self.advance_payment_method == 'fixed':
                amount_type = 'fixed'
                amount = self.fixed_amount

            down_payment_base_lines = AccountTax._prepare_down_payment_lines(
                base_lines=base_lines,
                company=self.company_id,
                amount_type=amount_type,
                amount=amount,
                computation_key=f'down_payment,{self.id}',
            )

            # Update the sale order.
            order._create_down_payment_section_line_if_needed()
            so_lines = order._create_down_payment_lines_from_base_lines(down_payment_base_lines)

            # Create the invoice.
            invoice_values = self.with_context(accounts=[
                base_line['account_id'] or self._get_down_payment_account(base_line['product_id'])
                for base_line in down_payment_base_lines
            ])._prepare_down_payment_invoice_values(
                order=order,
                so_lines=so_lines,
            )
            invoice_sudo = self.env['account.move'].sudo().create(invoice_values)

            # Unsudo the invoice after creation if not already sudoed
            invoice = invoice_sudo.sudo(self.env.su)
            poster = self.env.user._is_internal() and self.env.user.id or SUPERUSER_ID
            invoice.with_user(poster).message_post_with_source(
                'mail.message_origin_link',
                render_values={'self': invoice, 'origin': order},
                subtype_xmlid='mail.mt_note',
            )

            title = _("Down payment invoice")
            order.with_user(poster).message_post(
                body=_("%s has been created", invoice._get_html_link(title=title)),
            )

            return invoice