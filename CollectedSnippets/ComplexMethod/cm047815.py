def _get_autoprint_done_report_actions(self):
        """ Reports to auto-print when MO is marked as done
        """
        report_actions = []
        productions_to_print = self.filtered(lambda p: p.picking_type_id.auto_print_done_production_order)
        if productions_to_print:
            action = self.env.ref("mrp.action_report_production_order").report_action(productions_to_print.ids, config=False)
            clean_action(action, self.env)
            report_actions.append(action)
        productions_to_print = self.filtered(lambda p: p.picking_type_id.auto_print_done_mrp_product_labels)
        productions_by_print_formats = productions_to_print.grouped(lambda p: p.picking_type_id.mrp_product_label_to_print)
        for print_format in productions_to_print.picking_type_id.mapped('mrp_product_label_to_print'):
            labels_to_print = productions_by_print_formats.get(print_format)
            if print_format == 'pdf':
                action = self.env.ref("mrp.action_report_finished_product").report_action(labels_to_print.ids, config=False)
                clean_action(action, self.env)
                report_actions.append(action)
            elif print_format == 'zpl':
                action = self.env.ref("mrp.label_manufacture_template").report_action(labels_to_print.ids, config=False)
                clean_action(action, self.env)
                report_actions.append(action)
        if self.env.user.has_group('mrp.group_mrp_reception_report'):
            reception_reports_to_print = self.filtered(
                lambda p: p.picking_type_id.auto_print_mrp_reception_report
                          and p.picking_type_id.code == 'mrp_operation'
                          and p.move_finished_ids.move_dest_ids
            )
            if reception_reports_to_print:
                action = self.env.ref('stock.stock_reception_report_action').report_action(reception_reports_to_print, config=False)
                action['context'] = dict({'default_production_ids': reception_reports_to_print.ids}, **self.env.context)
                clean_action(action, self.env)
                report_actions.append(action)
            reception_labels_to_print = self.filtered(lambda p: p.picking_type_id.auto_print_mrp_reception_report_labels and p.picking_type_id.code == 'mrp_operation')
            if reception_labels_to_print:
                moves_to_print = reception_labels_to_print.move_finished_ids.move_dest_ids
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
        if self.env.user.has_group('stock.group_production_lot'):
            productions_to_print = self.filtered(lambda p: p.picking_type_id.auto_print_done_mrp_lot and p.move_finished_ids.move_line_ids.lot_id)
            productions_by_print_formats = productions_to_print.grouped(lambda p: p.picking_type_id.done_mrp_lot_label_to_print)
            for print_format in productions_to_print.picking_type_id.mapped('done_mrp_lot_label_to_print'):
                lots_to_print = productions_by_print_formats.get(print_format)
                lots_to_print = lots_to_print.move_finished_ids.move_line_ids.mapped('lot_id')
                if print_format == 'pdf':
                    action = self.env.ref("stock.action_report_lot_label").report_action(lots_to_print.ids, config=False)
                    clean_action(action, self.env)
                    report_actions.append(action)
                elif print_format == 'zpl':
                    action = self.env.ref("stock.label_lot_template").report_action(lots_to_print.ids, config=False)
                    clean_action(action, self.env)
                    report_actions.append(action)
        return report_actions