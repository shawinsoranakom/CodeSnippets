def _prepare_qty_received(self):
        from_stock_lines = self.filtered(lambda order_line: order_line.qty_received_method == 'stock_moves')
        received_qties = super(PurchaseOrderLine, self - from_stock_lines)._prepare_qty_received()
        for line in self:
            if line.qty_received_method == 'stock_moves':
                total = 0.0
                # In case of a BOM in kit, the products delivered do not correspond to the products in
                # the PO. Therefore, we can skip them since they will be handled later on.
                for move in line._get_po_line_moves():
                    if move.state == 'done':
                        if move._is_purchase_return():
                            if not move.origin_returned_move_id or move.to_refund:
                                total -= move.product_uom._compute_quantity(move.quantity, line.product_uom_id, rounding_method='HALF-UP')
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                            # Edge case: the dropship is returned to the stock, no to the supplier.
                            # In this case, the received quantity on the PO is set although we didn't
                            # receive the product physically in our stock. To avoid counting the
                            # quantity twice, we do nothing.
                            pass
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_purchase_return() and not move.to_refund:
                            pass
                        else:
                            total += move.product_uom._compute_quantity(move.quantity, line.product_uom_id, rounding_method='HALF-UP')
                line._track_qty_received(total)
                received_qties[line] = total
        return received_qties