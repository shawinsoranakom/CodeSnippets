def _prepare_analytic_lines(self):
        """ Note: This method is called only on the move.line that having an analytic distribution, and
            so that should create analytic entries.
        """
        values_list = super()._prepare_analytic_lines()

        # filter the move lines that can be reinvoiced: a cost (negative amount) analytic line without SO line but with a product can be reinvoiced
        move_to_reinvoice = self.env['account.move.line']
        if len(values_list) > 0:
            for index, move_line in enumerate(self):
                values = values_list[index]
                if 'so_line' not in values:
                    if move_line._sale_can_be_reinvoice():
                        move_to_reinvoice |= move_line

        # insert the sale line in the create values of the analytic entries
        if move_to_reinvoice.filtered(lambda aml: not aml.move_id.reversed_entry_id and aml.product_id):  # only if the move line is not a reversal one
            map_sale_line_per_move = move_to_reinvoice._sale_create_reinvoice_sale_line()
            for values in values_list:
                sale_line = map_sale_line_per_move.get(values.get('move_line_id'))
                if sale_line:
                    values['so_line'] = sale_line.id

        return values_list