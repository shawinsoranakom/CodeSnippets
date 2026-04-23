def write(self, vals):
        if 'odometer' in vals and any(vehicle.odometer > vals['odometer'] for vehicle in self):
            raise UserError(_('The odometer value cannot be lower than the previous one.'))

        if 'driver_id' in vals and vals['driver_id']:
            driver_id = vals['driver_id']
            for vehicle in self.filtered(lambda v: v.driver_id.id != driver_id):
                vehicle.create_driver_history(vals)
                if vehicle.driver_id:
                    vehicle.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=vehicle.manager_id.id or self.env.user.id,
                        note=_('Specify the End date of %s', vehicle.driver_id.name))

        if 'future_driver_id' in vals and vals['future_driver_id']:
            future_driver = vals['future_driver_id']
            state_waiting_list = self.env.ref('fleet.fleet_vehicle_state_waiting_list', raise_if_not_found=False)
            state_new_request = self.env.ref('fleet.fleet_vehicle_state_new_request', raise_if_not_found=False)
            vehicle_types = set(self.filtered(lambda vehicle: not state_waiting_list or\
                                vals.get('state_id', vehicle.state_id.id) not in [state_waiting_list.id, state_new_request.id]).mapped('vehicle_type'))
            if vehicle_types:
                vehicle_read_group = dict(self.env['fleet.vehicle']._read_group(
                    domain=[('driver_id', '=', future_driver), ('vehicle_type', 'in', vehicle_types), ('id', 'not in', self.ids)],
                    groupby=['vehicle_type'],
                    aggregates=['id:recordset'])
                )
                if 'bike' in vehicle_read_group:
                    vehicle_read_group['bike'].write({'plan_to_change_bike': True})
                if 'car' in vehicle_read_group:
                    vehicle_read_group['car'].write({'plan_to_change_car': True})

        if 'active' in vals and not vals['active']:
            self.env['fleet.vehicle.log.contract'].search([('vehicle_id', 'in', self.ids)]).active = False
            self.env['fleet.vehicle.log.services'].search([('vehicle_id', 'in', self.ids)]).active = False

        res = super(FleetVehicle, self).write(vals)
        return res