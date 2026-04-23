def _onchange_serial_number(self):
        """ When the user is encoding a move line for a tracked product, we apply some logic to
        help him. This includes:
            - automatically switch `quantity` to 1.0
            - warn if he has already encoded `lot_name` in another move line
            - warn (and update if appropriate) if the SN is in a different source location than selected
        """
        res = {}
        if self.product_id.tracking == 'serial':
            if not self.quantity:
                self.quantity = 1

            message = None
            if self.lot_name or self.lot_id:
                move_lines_to_check = self._get_similar_move_lines() - self
                if self.lot_name:
                    counter = Counter([line.lot_name for line in move_lines_to_check])
                    if counter.get(self.lot_name) and counter[self.lot_name] > 1:
                        message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                    elif not self.lot_id:
                        lots = self.env['stock.lot'].search([('product_id', '=', self.product_id.id),
                                                             ('name', '=', self.lot_name),
                                                             '|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])
                        quants = lots.quant_ids.filtered(lambda q: q.quantity != 0 and q.location_id.usage in ['customer', 'internal', 'transit'])
                        if quants:
                            message = _(
                                'Serial number (%(serial_number)s) already exists in location(s): %(location_list)s. Please correct the serial number encoded.',
                                serial_number=self.lot_name,
                                location_list=quants.location_id.mapped('display_name')
                            )
                elif self.lot_id:
                    counter = Counter([line.lot_id.id for line in move_lines_to_check])
                    if counter.get(self.lot_id.id) and counter[self.lot_id.id] > 1:
                        message = _('You cannot use the same serial number twice. Please correct the serial numbers encoded.')
                    else:
                        # check if in correct source location
                        message, recommended_location = self.env['stock.quant'].sudo()._check_serial_number(
                            self.product_id, self.lot_id, self.company_id, self.location_id, self.picking_id.location_id)
                        if recommended_location:
                            self.location_id = recommended_location
            if message:
                res['warning'] = {'title': _('Warning'), 'message': message}
        return res