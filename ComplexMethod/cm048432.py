def _action_done(self):
        """ This method is called during a move's `action_done`. It'll actually move a quant from
        the source location to the destination location, and unreserve if needed in the source
        location.

        This method is intended to be called on all the move lines of a move. This method is not
        intended to be called when editing a `done` move (that's what the override of `write` here
        is done.
        """

        # First, we loop over all the move lines to do a preliminary check: `quantity` should not
        # be negative and, according to the presence of a picking type or a linked inventory
        # adjustment, enforce some rules on the `lot_id` field. If `quantity` is null, we unlink
        # the line. It is mandatory in order to free the reservation and correctly apply
        # `action_done` on the next move lines.
        ml_ids_tracked_without_lot = OrderedSet()
        ml_ids_to_delete = OrderedSet()
        ml_ids_to_create_lot = OrderedSet()
        ml_ids_to_check = defaultdict(OrderedSet)

        for ml in self:
            # Check here if `ml.quantity` respects the rounding of `ml.product_uom_id`.
            uom_qty = ml.product_uom_id.round(ml.quantity, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit')
            quantity = float_round(ml.quantity, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, quantity, precision_digits=precision_digits) != 0:
                raise UserError(_('The quantity done for the product "%(product)s" doesn\'t respect the rounding precision '
                                  'defined on the unit of measure "%(unit)s". Please change the quantity done or the '
                                  'rounding precision of your unit of measure.',
                                  product=ml.product_id.display_name, unit=ml.product_uom_id.name))

            qty_done_float_compared = ml.product_uom_id.compare(ml.quantity, 0)
            if qty_done_float_compared > 0:
                if ml.product_id.tracking == 'none':
                    continue
                picking_type_id = ml.move_id.picking_type_id
                if not ml._exclude_requiring_lot():
                    ml_ids_tracked_without_lot.add(ml.id)
                    continue
                if not picking_type_id or ml.lot_id or (not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots):
                    # If the user disabled both `use_create_lots` and `use_existing_lots`
                    # checkboxes on the picking type, he's allowed to enter tracked
                    # products without a `lot_id`.
                    continue
                if picking_type_id.use_create_lots:
                    ml_ids_to_check[(ml.product_id, ml.company_id)].add(ml.id)
                else:
                    ml_ids_tracked_without_lot.add(ml.id)

            elif qty_done_float_compared < 0:
                raise UserError(_('No negative quantities allowed'))
            elif not ml.is_inventory:
                ml_ids_to_delete.add(ml.id)

        for (product, _company), mls in ml_ids_to_check.items():
            mls = self.env['stock.move.line'].browse(mls)
            lots = self.env['stock.lot'].search([
                '|', ('company_id', '=', False), ('company_id', '=', ml.company_id.id),
                ('product_id', '=', product.id),
                ('name', 'in', mls.mapped('lot_name')),
            ])
            lots = {lot.name: lot for lot in lots}
            for ml in mls:
                lot = lots.get(ml.lot_name)
                if lot:
                    ml.lot_id = lot.id
                elif ml.lot_name:
                    ml_ids_to_create_lot.add(ml.id)
                else:
                    ml_ids_tracked_without_lot.add(ml.id)

        if ml_ids_tracked_without_lot:
            mls_tracked_without_lot = self.env['stock.move.line'].browse(ml_ids_tracked_without_lot)
            products_list = "\n".join(f"- {product_name}" for product_name in mls_tracked_without_lot.mapped("product_id.display_name"))
            raise UserError(
                _(
                    "You need to supply a Lot/Serial Number for product:\n%(products)s",
                    products=products_list,
                ),
            )
        if ml_ids_to_create_lot:
            self.env['stock.move.line'].browse(ml_ids_to_create_lot)._create_and_assign_production_lot()

        mls_to_delete = self.env['stock.move.line'].browse(ml_ids_to_delete)
        mls_to_delete.unlink()

        mls_todo = (self - mls_to_delete)
        mls_todo._check_company()

        # Now, we can actually move the quant.
        ml_ids_to_ignore = OrderedSet()
        quants_cache = self.env['stock.quant']._get_quants_by_products_locations(
            mls_todo.product_id, mls_todo.location_id | mls_todo.location_dest_id,
            extra_domain=['|', ('lot_id', 'in', mls_todo.lot_id.ids), ('lot_id', '=', False)])

        # Prepare package history records before any actual move
        if not self.env.context.get('ignore_dest_packages'):
            package_history_vals = mls_todo._prepare_package_history_vals()
            if package_history_vals:
                self.env['stock.package.history'].create(package_history_vals)

        for ml in mls_todo.with_context(quants_cache=quants_cache):
            # if this move line is force assigned, unreserve elsewhere if needed
            ml._synchronize_quant(-ml.quantity_product_uom, ml.location_id, action="reserved")
            available_qty, in_date = ml._synchronize_quant(-ml.quantity_product_uom, ml.location_id)
            ml._synchronize_quant(ml.quantity_product_uom, ml.location_dest_id, package=ml.result_package_id, in_date=in_date)
            if available_qty < 0:
                ml.with_context(quants_cache=None)._free_reservation(
                    ml.product_id, ml.location_id,
                    abs(available_qty), lot_id=ml.lot_id, package_id=ml.package_id,
                    owner_id=ml.owner_id, ml_ids_to_ignore=ml_ids_to_ignore)
            ml_ids_to_ignore.add(ml.id)

        if not self.env.context.get('ignore_dest_packages'):
            mls_todo.result_package_id._apply_dest_to_package()

        # Reset the reserved quantity as we just moved it to the destination location.
        mls_todo.write({
            'date': fields.Datetime.now(),
        })