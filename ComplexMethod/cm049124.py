def init_purchase(cls, partner=None, confirm=False, products=None, taxes=None, company=False):
        date_planned = fields.Datetime.now() - timedelta(days=1)
        po_form = Form(cls.env['purchase.order'] \
                    .with_company(company or cls.env.company) \
                    .with_context(tracking_disable=True))
        po_form.partner_id = partner or cls.partner_a
        po_form.partner_ref = 'my_match_reference'

        for product in (products or []):
            with po_form.order_line.new() as line_form:
                line_form.product_id = product
                line_form.product_qty = 1
                line_form.product_uom_id = product.uom_id
                line_form.date_planned = date_planned
                if taxes:
                    line_form.tax_ids.clear()
                    for tax in taxes:
                        line_form.tax_ids.add(tax)

        rslt = po_form.save()

        if confirm:
            rslt.button_confirm()

        return rslt