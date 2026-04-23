def _get_revenues_items_from_sol(self, domain=None, with_action=True):
        sale_line_read_group = self.env['sale.order.line'].sudo()._read_group(
            self._get_profitability_sale_order_items_domain(domain),
            ['currency_id', 'product_id', 'is_downpayment'],
            ['id:array_agg', 'untaxed_amount_to_invoice:sum', 'untaxed_amount_invoiced:sum'],
        )
        display_sol_action = with_action and len(self) == 1 and self.env.user.has_group('sales_team.group_sale_salesman')
        revenues_dict = {}
        total_to_invoice = total_invoiced = 0.0
        data = []
        sequence_per_invoice_type = self._get_profitability_sequence_per_invoice_type()
        if sale_line_read_group:
            # Get conversion rate from currencies of the sale order lines to currency of project
            convert_company = self.company_id or self.env.company

            sols_per_product = defaultdict(lambda: [0.0, 0.0, []])
            downpayment_amount_invoiced = 0
            downpayment_sol_ids = []
            for currency, product, is_downpayment, sol_ids, untaxed_amount_to_invoice, untaxed_amount_invoiced in sale_line_read_group:
                if is_downpayment:
                    downpayment_amount_invoiced += currency._convert(untaxed_amount_invoiced, convert_company.currency_id, convert_company, round=False)
                    downpayment_sol_ids += sol_ids
                else:
                    sols_per_product[product.id][0] += currency._convert(untaxed_amount_to_invoice, convert_company.currency_id, convert_company)
                    sols_per_product[product.id][1] += currency._convert(untaxed_amount_invoiced, convert_company.currency_id, convert_company)
                    sols_per_product[product.id][2] += sol_ids
            if downpayment_amount_invoiced:
                downpayments_data = {
                    'id': 'downpayments',
                    'sequence': sequence_per_invoice_type['downpayments'],
                    'invoiced': downpayment_amount_invoiced,
                    'to_invoice': -downpayment_amount_invoiced,
                }
                if with_action and (
                    self.env.user.has_group('sales_team.group_sale_salesman_all_leads,')
                    or self.env.user.has_group('account.group_account_invoice,')
                    or self.env.user.has_group('account.group_account_readonly')
                ):
                    invoices = self.env['account.move'].search([('line_ids.sale_line_ids', 'in', downpayment_sol_ids)])
                    args = ['downpayments', [('id', 'in', invoices.ids)]]
                    if len(invoices) == 1:
                        args.append(invoices.id)
                    downpayments_data['action'] = {
                        'name': 'action_profitability_items',
                        'type': 'object',
                        'args': json.dumps(args),
                    }
                data += [downpayments_data]
                total_invoiced += downpayment_amount_invoiced
                total_to_invoice -= downpayment_amount_invoiced
            product_read_group = self.env['product.product'].sudo()._read_group(
                [('id', 'in', list(sols_per_product))],
                ['invoice_policy', 'service_type', 'type'],
                ['id:array_agg'],
            )
            service_policy_to_invoice_type = self._get_service_policy_to_invoice_type()
            general_to_service_map = self.env['product.template']._get_general_to_service_map()
            for invoice_policy, service_type, type_, product_ids in product_read_group:
                service_policy = None
                if type_ == 'service':
                    service_policy = general_to_service_map.get(
                        (invoice_policy, service_type),
                        'ordered_prepaid')
                for product_id, (amount_to_invoice, amount_invoiced, sol_ids) in sols_per_product.items():
                    if product_id in product_ids:
                        invoice_type = service_policy_to_invoice_type.get(service_policy, 'materials')
                        revenue = revenues_dict.setdefault(invoice_type, {'invoiced': 0.0, 'to_invoice': 0.0})
                        revenue['to_invoice'] += amount_to_invoice
                        total_to_invoice += amount_to_invoice
                        revenue['invoiced'] += amount_invoiced
                        total_invoiced += amount_invoiced
                        if display_sol_action and invoice_type in ['service_revenues', 'materials']:
                            revenue.setdefault('record_ids', []).extend(sol_ids)

            if display_sol_action:
                section_name = 'materials'
                materials = revenues_dict.get(section_name, {})
                sale_order_items = self.env['sale.order.line'] \
                    .browse(materials.pop('record_ids', [])) \
                    ._filtered_access('read')
                if sale_order_items:
                    args = [section_name, [('id', 'in', sale_order_items.ids)]]
                    if len(sale_order_items) == 1:
                        args.append(sale_order_items.id)
                    action_params = {
                        'name': 'action_profitability_items',
                        'type': 'object',
                        'args': json.dumps(args),
                    }
                    if len(sale_order_items) == 1:
                        action_params['res_id'] = sale_order_items.id
                    materials['action'] = action_params
        sequence_per_invoice_type = self._get_profitability_sequence_per_invoice_type()
        data += [{
            'id': invoice_type,
            'sequence': sequence_per_invoice_type[invoice_type],
            **vals,
        } for invoice_type, vals in revenues_dict.items()]
        return {
            'data': data,
            'total': {'to_invoice': total_to_invoice, 'invoiced': total_invoiced},
        }