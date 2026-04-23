def _get_autoprint_report_actions(self):
        report_actions = []
        pickings_to_print = self.filtered(lambda p: p.picking_type_id.auto_print_delivery_slip)
        if pickings_to_print:
            action = self.env.ref("stock.action_report_delivery").report_action(pickings_to_print.ids, config=False)
            clean_action(action, self.env)
            report_actions.append(action)
        pickings_print_return_slip = self.filtered(lambda p: p.picking_type_id.auto_print_return_slip)
        if pickings_print_return_slip:
            action = self.env.ref("stock.return_label_report").report_action(pickings_print_return_slip.ids, config=False)
            clean_action(action, self.env)
            report_actions.append(action)

        if self.env.user.has_group('stock.group_reception_report'):
            reception_reports_to_print = self.filtered(
                lambda p: p.picking_type_id.auto_print_reception_report
                          and p.picking_type_id.code != 'outgoing'
                          and p.move_ids.move_dest_ids
            )
            if reception_reports_to_print:
                action = self.env.ref('stock.stock_reception_report_action').report_action(reception_reports_to_print, config=False)
                clean_action(action, self.env)
                report_actions.append(action)
            reception_labels_to_print = self.filtered(lambda p: p.picking_type_id.auto_print_reception_report_labels and p.picking_type_id.code != 'outgoing')
            if reception_labels_to_print:
                moves_to_print = reception_labels_to_print.move_ids.move_dest_ids
                if moves_to_print:
                    # needs to be string to support python + js calls to report
                    quantities = ','.join(str(qty) for qty in moves_to_print.mapped(lambda m: math.ceil(m.product_uom_qty)))
                    data = {
                        'docids': moves_to_print.ids,
                        'quantity': quantities,
                    }
                    action = self.env.ref('stock.label_picking').report_action(moves_to_print, data=data, config=False)
                    clean_action(action, self.env)
                    report_actions.append(action)
        pickings_print_product_label = self.filtered(lambda p: p.picking_type_id.auto_print_product_labels)
        pickings_by_print_formats = pickings_print_product_label.grouped(lambda p: p.picking_type_id.product_label_format)
        for print_format in pickings_print_product_label.picking_type_id.mapped("product_label_format"):
            pickings = pickings_by_print_formats.get(print_format)
            wizard = self.env['product.label.layout'].create({
                'product_ids': pickings.move_ids.product_id.ids,
                'move_ids': pickings.move_ids.ids,
                'move_quantity': 'move',
                'print_format': pickings.picking_type_id.product_label_format,
            })
            action = wizard.process()
            if action:
                clean_action(action, self.env)
                report_actions.append(action)
        if self.env.user.has_group('stock.group_production_lot'):
            pickings_print_lot_label = self.filtered(lambda p: p.picking_type_id.auto_print_lot_labels and p.move_line_ids.lot_id)
            pickings_by_print_formats = pickings_print_lot_label.grouped(lambda p: p.picking_type_id.lot_label_format)
            for print_format in pickings_print_lot_label.picking_type_id.mapped("lot_label_format"):
                pickings = pickings_by_print_formats.get(print_format)
                wizard = self.env['lot.label.layout'].create({
                    'move_line_ids': pickings.move_line_ids.ids,
                    'label_quantity': 'lots' if '_lots' in print_format else 'units',
                    'print_format': '4x12' if '4x12' in print_format else 'zpl',
                })
                action = wizard.process()
                if action:
                    clean_action(action, self.env)
                    report_actions.append(action)
        if self.env.user.has_group('stock.group_tracking_lot'):
            pickings_print_packages = self.filtered(lambda p: p.picking_type_id.auto_print_packages and p.move_line_ids.result_package_id)
            if pickings_print_packages:
                action = self.env.ref("stock.action_report_picking_packages").report_action(pickings_print_packages.ids, config=False)
                clean_action(action, self.env)
                report_actions.append(action)
        return report_actions