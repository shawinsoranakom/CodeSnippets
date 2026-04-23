def pre_button_mark_done(self):
        self._button_mark_done_sanity_checks()
        production_auto_ids = set()
        production_missing_lot_ids = set()
        for production in self:
            if production._auto_production_checks():
                production_auto_ids.add(production.id)
            elif not production.lot_producing_ids:
                production_missing_lot_ids.add(production.id)

        if production_missing_lot_ids:
            if len(production_missing_lot_ids) > 1:
                raise UserError(_("You need to generate Lot/Serial Number(s) to mark as done some productions"))
            return self.env['mrp.production'].browse(production_missing_lot_ids).action_generate_serial()

        productions_auto = self.env['mrp.production'].browse(production_auto_ids)
        for production in productions_auto:
            production._set_quantities()

        self.move_raw_ids.filtered(lambda m: m.manual_consumption and not m.picked).picked = True

        # Produce by-products also for not auto productions.
        (self - productions_auto)._mark_byproducts_as_produced()

        consumption_issues = self._get_consumption_issues()
        if consumption_issues:
            return self._action_generate_consumption_wizard(consumption_issues)

        quantity_issues = self._get_quantity_produced_issues()
        if quantity_issues:
            mo_ids_always = []  # we need to pass the mo.ids in a context, so collect them to avoid looping through the list twice
            mos_ask = []  # we need to pass a list of mo records to the backorder wizard, so collect records
            for mo in quantity_issues:
                if mo.picking_type_id.create_backorder == "always":
                    mo_ids_always.append(mo.id)
                elif mo.picking_type_id.create_backorder == "ask":
                    mos_ask.append(mo)
            if mos_ask:
                # any "never" MOs will be passed to the wizard, but not considered for being backorder-able, always backorder mos are hack forced via context
                return self.with_context(always_backorder_mo_ids=mo_ids_always)._action_generate_backorder_wizard(mos_ask)
            elif mo_ids_always:
                # we have to pass all the MOs that the nevers/no issue MOs are also passed to be "mark done" without a backorder
                res = self.with_context(skip_backorder=True, mo_ids_to_backorder=mo_ids_always).button_mark_done()
                if res is not True:
                    res['context'] = dict(res.get('context', {}), marked_as_done=all(mo.state == 'done' for mo in self))
                return res if self._should_return_records() else True
        return True