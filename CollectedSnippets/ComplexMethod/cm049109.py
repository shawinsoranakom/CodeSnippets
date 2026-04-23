def _get_profitability_items_from_aal(self, profitability_items, with_action=True):
        if not self.allow_timesheets:
            total_invoiced = total_to_invoice = 0.0
            revenue_data = []
            for revenue in profitability_items['revenues']['data']:
                if revenue['id'] in ['billable_fixed', 'billable_time', 'billable_milestones', 'billable_manual']:
                    continue
                total_invoiced += revenue['invoiced']
                total_to_invoice += revenue['to_invoice']
                revenue_data.append(revenue)
            profitability_items['revenues'] = {
                'data': revenue_data,
                'total': {'to_invoice': total_to_invoice, 'invoiced': total_invoiced},
            }
            return profitability_items
        aa_line_read_group = self.env['account.analytic.line'].sudo()._read_group(
            self.sudo()._get_profitability_aal_domain(),
            ['timesheet_invoice_type', 'timesheet_invoice_id', 'currency_id', 'category'],
            ['amount:sum', 'id:array_agg'],
        )
        can_see_timesheets = with_action and len(self) == 1 and self.env.user.has_group('hr_timesheet.group_hr_timesheet_approver')
        revenues_dict = {}
        costs_dict = {}
        total_revenues = {'invoiced': 0.0, 'to_invoice': 0.0}
        total_costs = {'billed': 0.0, 'to_bill': 0.0}
        convert_company = self.company_id or self.env.company
        for timesheet_invoice_type, _dummy, currency, category, amount, ids in aa_line_read_group:
            if category == 'vendor_bill':
                continue  # This is done to prevent expense duplication with product re-invoice policies
            amount = currency._convert(amount, self.currency_id, convert_company)
            invoice_type = timesheet_invoice_type
            cost = costs_dict.setdefault(invoice_type, {'billed': 0.0, 'to_bill': 0.0})
            revenue = revenues_dict.setdefault(invoice_type, {'invoiced': 0.0, 'to_invoice': 0.0})
            if amount < 0:  # cost
                cost['billed'] += amount
                total_costs['billed'] += amount
            else:  # revenues
                revenue['invoiced'] += amount
                total_revenues['invoiced'] += amount
            if can_see_timesheets and invoice_type not in ['other_costs', 'other_revenues']:
                cost.setdefault('record_ids', []).extend(ids)
                revenue.setdefault('record_ids', []).extend(ids)
        action_name = None
        if can_see_timesheets:
            action_name = 'action_profitability_items'

        def get_timesheets_action(invoice_type, record_ids):
            args = [invoice_type, [('id', 'in', record_ids)]]
            if len(record_ids) == 1:
                args.append(record_ids[0])
            return {'name': action_name, 'type': 'object', 'args': json.dumps(args)}

        sequence_per_invoice_type = self._get_profitability_sequence_per_invoice_type()

        def convert_dict_into_profitability_data(d, cost=True):
            profitability_data = []
            key1, key2 = ['to_bill', 'billed'] if cost else ['to_invoice', 'invoiced']
            for invoice_type, vals in d.items():
                if not vals[key1] and not vals[key2]:
                    continue
                record_ids = vals.pop('record_ids', [])
                data = {'id': invoice_type, 'sequence': sequence_per_invoice_type[invoice_type], **vals}
                if record_ids:
                    if invoice_type not in ['other_costs', 'other_revenues'] and can_see_timesheets:  # action to see the timesheets
                        action = get_timesheets_action(invoice_type, record_ids)
                        data['action'] = action
                profitability_data.append(data)
            return profitability_data

        def merge_profitability_data(a, b):
            return {
                'data': a['data'] + b['data'],
                'total': {key: a['total'][key] + b['total'][key] for key in a['total'] if key in b['total']}
            }

        for revenue in profitability_items['revenues']['data']:
            revenue_id = revenue['id']
            aal_revenue = revenues_dict.pop(revenue_id, {})
            revenue['to_invoice'] += aal_revenue.get('to_invoice', 0.0)
            revenue['invoiced'] += aal_revenue.get('invoiced', 0.0)
            record_ids = aal_revenue.get('record_ids', [])
            if can_see_timesheets and record_ids:
                action = get_timesheets_action(revenue_id, record_ids)
                revenue['action'] = action

        for cost in profitability_items['costs']['data']:
            cost_id = cost['id']
            aal_cost = costs_dict.pop(cost_id, {})
            cost['to_bill'] += aal_cost.get('to_bill', 0.0)
            cost['billed'] += aal_cost.get('billed', 0.0)
            record_ids = aal_cost.get('record_ids', [])
            if can_see_timesheets and record_ids:
                cost['action'] = get_timesheets_action(cost_id, record_ids)

        profitability_items['revenues'] = merge_profitability_data(
            profitability_items['revenues'],
            {'data': convert_dict_into_profitability_data(revenues_dict, False), 'total': total_revenues},
        )
        profitability_items['costs'] = merge_profitability_data(
            profitability_items['costs'],
            {'data': convert_dict_into_profitability_data(costs_dict), 'total': total_costs},
        )
        return profitability_items