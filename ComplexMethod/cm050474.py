def _prepare_base_line_for_taxes_computation(self):
        self.ensure_one()
        commercial_partner = self.order_id.partner_id.commercial_partner_id
        fiscal_position = self.order_id.fiscal_position_id
        line = self.with_company(self.order_id.company_id)
        account = line.product_id._get_product_accounts()['income'] or self.order_id.config_id.journal_id.default_account_id
        if not account:
            raise UserError(_(
                "Please define income account for this product: '%(product)s' (id:%(id)d).",
                product=line.product_id.name, id=line.product_id.id,
            ))

        if fiscal_position:
            account = fiscal_position.map_account(account)

        is_refund_order = line.order_id.is_refund or line.order_id.amount_total < 0.0
        is_refund_line = line.qty * line.price_unit < 0

        lang = line.order_id.partner_id.lang or self.env.user.lang
        product_name = line.with_context(lang=lang).full_product_name or line.product_id.with_context(lang=lang).display_name
        if line.product_id.description_sale:
            product_name += '\n' + line.product_id.with_context(lang=lang).description_sale
        return {
            **self.env['account.tax']._prepare_base_line_for_taxes_computation(
                line,
                partner_id=commercial_partner,
                currency_id=self.order_id.currency_id,
                rate=self.order_id.currency_rate,
                product_id=line.product_id,
                tax_ids=line.tax_ids_after_fiscal_position,
                price_unit=line.price_unit,
                quantity=line.qty * (-1 if is_refund_order else 1),
                discount=line.discount,
                account_id=account,
                is_refund=is_refund_line,
                sign=1 if is_refund_order else -1,
            ),
            'uom_id': line.product_uom_id,
            'name': product_name,
        }