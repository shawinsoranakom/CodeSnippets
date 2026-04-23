def action_merge(self):
        all_origin = []
        all_vendor_references = []
        rfq_to_merge = self.filtered(lambda r: r.state in ['draft', 'sent'])

        # Group RFQs by vendor
        if len(rfq_to_merge) < 2:
            raise UserError(_("Please select at least two purchase orders with state RFQ and RFQ sent to merge."))

        rfqs_grouped = defaultdict(lambda: self.env['purchase.order'])
        for rfq in rfq_to_merge:
            key = self._prepare_grouped_data(rfq)
            rfqs_grouped[key] += rfq

        bunches_of_rfq_to_be_merge = list(rfqs_grouped.values())
        if all(len(rfq_bunch) == 1 for rfq_bunch in list(bunches_of_rfq_to_be_merge)):
            raise UserError(_("In selected purchase order to merge these details must be same\nVendor, currency, destination, dropship address and agreement"))
        bunches_of_rfq_to_be_merge = [rfqs for rfqs in bunches_of_rfq_to_be_merge if len(rfqs) > 1]

        merged_rfq_ids = []

        for rfqs in bunches_of_rfq_to_be_merge:
            if len(rfqs) <= 1:
                continue
            oldest_rfq = min(rfqs, key=lambda r: r.date_order)
            if oldest_rfq:
                # Merge RFQs into the oldest purchase order
                rfqs -= oldest_rfq
                for rfq_line in rfqs.order_line:
                    existing_line = oldest_rfq.order_line.filtered(lambda l: l.display_type not in ['line_section', 'line_subsection', 'line_note'] and
                                                                                l.product_id == rfq_line.product_id and
                                                                                l.product_uom_id == rfq_line.product_uom_id and
                                                                                l.analytic_distribution == rfq_line.analytic_distribution and
                                                                                l.discount == rfq_line.discount and
                                                                                abs(l.date_planned - rfq_line.date_planned).total_seconds() <= 86400  # 24 hours in seconds
                                                                        )
                    if len(existing_line) > 1:
                        existing_line[0].product_qty += sum(existing_line[1:].mapped('product_qty'))
                        existing_line[1:].unlink()
                        existing_line = existing_line[0]

                    if existing_line:
                        existing_line._merge_po_line(rfq_line)
                    else:
                        rfq_line.order_id = oldest_rfq

                # Merge source documents and vendor references
                all_origin = rfqs.mapped('origin')
                all_vendor_references = rfqs.mapped('partner_ref')

                oldest_rfq.origin = ', '.join(filter(None, [oldest_rfq.origin, *all_origin]))
                oldest_rfq.partner_ref = ', '.join(filter(None, [oldest_rfq.partner_ref, *all_vendor_references]))

                rfq_names = rfqs.mapped('name')
                merged_names = ", ".join(rfq_names)
                oldest_rfq_message = _("RFQ merged with %(oldest_rfq_name)s and %(cancelled_rfq)s", oldest_rfq_name=oldest_rfq.name, cancelled_rfq=merged_names)

                for rfq in rfqs:
                    cancelled_rfq_message = _("RFQ merged with %s", oldest_rfq._get_html_link())
                    rfq.message_post(body=cancelled_rfq_message)
                oldest_rfq.message_post(body=oldest_rfq_message)

                rfqs.filtered(lambda r: r.state != 'cancel').button_cancel()
                oldest_rfq._merge_alternative_po(rfqs)

                # Keep the oldest RFQ IDs
                merged_rfq_ids.append(oldest_rfq.id)

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'list,kanban,form',
            'res_model': 'purchase.order',
        }
        if len(merged_rfq_ids) == 1:
            action['res_id'] = merged_rfq_ids[0]
            action['view_mode'] = 'form'
        else:
            action['name'] = _("Merged RFQs")
            action['domain'] = [('id', 'in', merged_rfq_ids)]
        return action