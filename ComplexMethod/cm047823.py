def write(self, vals):
        values = vals
        new_workcenter = False
        if 'qty_produced' in values:
            for wo in self:
                if wo.state in ['done', 'cancel']:
                    raise UserError(_('You cannot change the quantity produced of a work order that is in done or cancel state.'))
                elif wo.product_uom_id.compare(values['qty_produced'], 0) < 0:
                    raise UserError(_('The quantity produced must be positive.'))

        workorders_with_new_wc = self.env['mrp.workorder']
        if 'production_id' in values and any(values['production_id'] != w.production_id.id for w in self):
            raise UserError(_('You cannot link this work order to another manufacturing order.'))
        if 'workcenter_id' in values:
            new_workcenter = self.env['mrp.workcenter'].browse(values['workcenter_id'])
            for workorder in self:
                if workorder.workcenter_id.id != values['workcenter_id']:
                    if workorder.state in ('done', 'cancel'):
                        raise UserError(_('You cannot change the workcenter of a work order that is done.'))
                    workorder.leave_id.resource_id = new_workcenter.resource_id
                    if workorder.state == 'progress':
                        continue
                    workorders_with_new_wc |= workorder
        if 'date_start' in values or 'date_finished' in values:
            for workorder in self:
                date_start = fields.Datetime.to_datetime(values.get('date_start', workorder.date_start))
                date_finished = fields.Datetime.to_datetime(values.get('date_finished', workorder.date_finished))
                if date_start and date_finished and date_start > date_finished:
                    raise UserError(_('The planned end date of the work order cannot be prior to the planned start date, please correct this to save the work order.'))
                if 'duration_expected' not in values and not self.env.context.get('bypass_duration_calculation'):
                    if values.get('date_start') and values.get('date_finished'):
                        computed_finished_time = workorder._calculate_date_finished(date_start=date_start, new_workcenter=new_workcenter)
                        values['date_finished'] = computed_finished_time
                    elif date_start and date_finished:
                        computed_duration = workorder._calculate_duration_expected(date_start=date_start, date_finished=date_finished)
                        values['duration_expected'] = computed_duration
                # Update MO dates if the start date of the first WO or the
                # finished date of the last WO is update.
                if workorder == workorder.production_id.workorder_ids[0] and 'date_start' in values:
                    if values['date_start']:
                        workorder.production_id.with_context(force_date=True).write({
                            'date_start': fields.Datetime.to_datetime(values['date_start'])
                        })
                if workorder == workorder.production_id.workorder_ids[-1] and 'date_finished' in values:
                    if values['date_finished']:
                        workorder.production_id.with_context(force_date=True).write({
                            'date_finished': fields.Datetime.to_datetime(values['date_finished'])
                        })

        res = super().write(values)
        productions = self.production_id.filtered(
            lambda p: p.product_uom_id.compare(values.get('qty_produced', 0), 0) > 0
        )
        if 'qty_produced' in values and productions:
            for production in productions:
                min_wo_qty = min(production.workorder_ids.mapped('qty_produced'))
                if production.product_uom_id.compare(min_wo_qty, 0) > 0:
                    production.workorder_ids.filtered(lambda w: w.state != 'done').qty_producing = min_wo_qty
            self._set_qty_producing()
        for workorder in workorders_with_new_wc:
            workorder.duration_expected = workorder._get_duration_expected()
            if workorder.date_start:
                workorder.date_finished = workorder._calculate_date_finished(new_workcenter=new_workcenter)

        return res