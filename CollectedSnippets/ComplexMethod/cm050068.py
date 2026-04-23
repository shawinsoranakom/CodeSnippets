def _post_process_link_to_purchase_order(self, invoice):
        # Override account.move
        try:
            invoice._check_move_for_group_ungroup_lines_by_tax()
        except UserError:
            return

        if (
            self.env.context.get('ungroup_lines')
            or not invoice.partner_id
            or not invoice.ubl_cii_xml_id
        ):
            return

        # Group lines
        if invoice.journal_id.type == 'sale':
            move_types = invoice.get_sale_types(include_receipts=True)
        else:
            move_types = invoice.get_purchase_types(include_receipts=True)
        last_bill_from_vendor = self.env['account.move'].search([
            ('move_type', 'in', move_types),
            ('partner_id', '=', invoice.partner_id.id),
            ('state', '=', 'posted'),
            ('id', '!=', invoice.id),
            *self.env['account.move']._check_company_domain(invoice.company_id),
        ], order='create_date desc', limit=1)
        if last_bill_from_vendor and last_bill_from_vendor._has_lines_grouped():
            invoice._group_lines_by_tax()