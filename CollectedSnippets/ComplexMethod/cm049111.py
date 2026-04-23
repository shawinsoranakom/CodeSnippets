def _compute_timesheet_invoice_type(self):
        for timesheet in self:
            if timesheet.project_id:  # AAL will be set to False
                invoice_type = False
                if not timesheet.so_line:
                    invoice_type = 'non_billable' if timesheet.project_id.billing_type != 'manually' else 'billable_manual'
                elif timesheet.so_line.product_id.type == 'service':
                    if timesheet.so_line.product_id.invoice_policy == 'delivery':
                        if timesheet.so_line.product_id.service_type == 'timesheet':
                            invoice_type = 'timesheet_revenues' if timesheet.amount > 0 and timesheet.unit_amount > 0 else 'billable_time'
                        else:
                            service_type = timesheet.so_line.product_id.service_type
                            invoice_type = f'billable_{service_type}' if service_type in ['milestones', 'manual'] else 'billable_fixed'
                    elif timesheet.so_line.product_id.invoice_policy == 'order':
                        invoice_type = 'billable_fixed'
                timesheet.timesheet_invoice_type = invoice_type
            else:
                if timesheet.amount >= 0 and timesheet.unit_amount >= 0:
                    if timesheet.so_line and timesheet.so_line.product_id.type == 'service':
                        timesheet.timesheet_invoice_type = 'service_revenues'
                    else:
                        timesheet.timesheet_invoice_type = 'other_revenues'
                else:
                    timesheet.timesheet_invoice_type = 'other_costs'