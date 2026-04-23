def _sale_create_reinvoice_sale_line(self):

        sale_order_map = self._sale_determine_order()

        sale_line_values_to_create = []  # the list of creation values of sale line to create.
        existing_sale_line_cache = {}  # in the sales_price-delivery case, we can reuse the same sale line. This cache will avoid doing a search each time the case happen
        # `map_move_sale_line` is map where
        #   - key is the move line identifier
        #   - value is either a sale.order.line record (existing case), or an integer representing the index of the sale line to create in
        #     the `sale_line_values_to_create` (not existing case, which will happen more often than the first one).
        map_move_sale_line = {}

        for move_line in self:
            sale_order = sale_order_map.get(move_line.id)

            # no reinvoice as no sales order was found
            if not sale_order:
                continue

            # raise if the sale order is not currently open
            if sale_order.state in ('draft', 'sent'):
                raise UserError(_(
                    "The Sales Order %(order)s to be reinvoiced must be validated before registering expenses.",
                    order=sale_order.name,
                ))
            elif sale_order.state == 'cancel':
                raise UserError(_(
                    "The Sales Order %(order)s to be reinvoiced is cancelled."
                    " You cannot register an expense on a cancelled Sales Order.",
                    order=sale_order.name,
                ))
            elif sale_order.locked:
                raise UserError(_(
                    "The Sales Order %(order)s to be reinvoiced is currently locked."
                    " You cannot register an expense on a locked Sales Order.",
                    order=sale_order.name,
                ))

            price = move_line._sale_get_invoice_price(sale_order)

            # find the existing sale.line or keep its creation values to process this in batch
            sale_line = None
            if (
                move_line.product_id.expense_policy == 'sales_price'
                and move_line.product_id.invoice_policy == 'delivery'
                and not self.env.context.get('force_split_lines')
            ):
                # for those case only, we can try to reuse one
                map_entry_key = (sale_order.id, move_line.product_id.id, price)  # cache entry to limit the call to search
                sale_line = existing_sale_line_cache.get(map_entry_key)
                if sale_line:  # already search, so reuse it. sale_line can be sale.order.line record or index of a "to create values" in `sale_line_values_to_create`
                    map_move_sale_line[move_line.id] = sale_line
                    existing_sale_line_cache[map_entry_key] = sale_line
                else:  # search for existing sale line
                    sale_line = self.env['sale.order.line'].search([
                        ('order_id', '=', sale_order.id),
                        ('price_unit', '=', price),
                        ('product_id', '=', move_line.product_id.id),
                        ('is_expense', '=', True),
                    ], limit=1)
                    if sale_line:  # found existing one, so keep the browse record
                        map_move_sale_line[move_line.id] = existing_sale_line_cache[map_entry_key] = sale_line
                    else:  # should be create, so use the index of creation values instead of browse record
                        # save value to create it
                        sale_line_values_to_create.append(move_line._sale_prepare_sale_line_values(sale_order, price))
                        # store it in the cache of existing ones
                        existing_sale_line_cache[map_entry_key] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line
                        # store it in the map_move_sale_line map
                        map_move_sale_line[move_line.id] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line

            else:  # save its value to create it anyway
                sale_line_values_to_create.append(move_line._sale_prepare_sale_line_values(sale_order, price))
                map_move_sale_line[move_line.id] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line

        # create the sale lines in batch
        new_sale_lines = self.env['sale.order.line'].create(sale_line_values_to_create)

        # build result map by replacing index with newly created record of sale.order.line
        result = {}
        for move_line_id, unknown_sale_line in map_move_sale_line.items():
            if isinstance(unknown_sale_line, int):  # index of newly created sale line
                result[move_line_id] = new_sale_lines[unknown_sale_line]
            elif isinstance(unknown_sale_line, models.BaseModel):  # already record of sale.order.line
                result[move_line_id] = unknown_sale_line
        return result